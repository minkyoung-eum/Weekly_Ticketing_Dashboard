import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os

# Page Config
st.set_page_config(
    page_title="항공사 노선별 통합 M/S 대시보드 (발매 & 공급)",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dynamic Date Logic
today = datetime.date.today()
current_monday = today - datetime.timedelta(days=today.weekday())
issue_start_date = current_monday - datetime.timedelta(weeks=5)
issue_end_date = current_monday - datetime.timedelta(days=1)

dep_start_m = today.replace(day=1)
dep_months = []
for i in range(5):
    m = (dep_start_m.month - 1 + i) % 12 + 1
    y = dep_start_m.year + (dep_start_m.month - 1 + i) // 12
    dep_months.append(f"{y}.{m:02d}월")

dep_range_str = f"{dep_months[0]} ~ {dep_months[-1]}"
issue_range_str = f"{issue_start_date.strftime('%Y.%m.%d')} ~ {issue_end_date.strftime('%Y.%m.%d')}"

# CSS Styling with KE Highlight (#00A1E9)
st.markdown("""
<style>
    .source-header-box {
        background-color: #e0f2fe;
        border-left: 5px solid #0284c7;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 14px;
        color: #0f172a;
        font-weight: 500;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-card-ke {
        background-color: #e0f2fe;
        border: 2px solid #00a1e9;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 3px 6px rgba(0,161,233,0.25);
    }
    .metric-title {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 24px;
        color: #1e293b;
        font-weight: 700;
    }
    .section-header {
        background-color: #1e3a8a;
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 17px;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar File Uploader Section
st.sidebar.header("📁 데이터 파일 업로드")

uploaded_iss = st.sidebar.file_uploader("1. 발매 데이터 (Ticketing-test_2.csv)", type=['csv'])
uploaded_wt = st.sidebar.file_uploader("2. 가중치 파일 (가중치 파일.csv)", type=['csv'])
uploaded_sup = st.sidebar.file_uploader("3. 공급 데이터 (공급.csv/xlsx)", type=['csv', 'xlsx'])

# Load Logic Function
@st.cache_data
def load_data_from_disk():
    df_iss, df_wt, df_sup = None, None, None
    if os.path.exists('Ticketing-test_2.csv'):
        df_iss = pd.read_csv('Ticketing-test_2.csv', low_memory=False)
    if os.path.exists('가중치 파일.csv'):
        df_wt = pd.read_csv('가중치 파일.csv')
    if os.path.exists('공급 (9월 1주).csv'):
        df_sup = pd.read_csv('공급 (9월 1주).csv', low_memory=False)
    elif os.path.exists('공급.xlsx'):
        df_sup = pd.read_excel('공급.xlsx', sheet_name='공급_RAW')
    return df_iss, df_wt, df_sup

disk_iss, disk_wt, disk_sup = load_data_from_disk()

# Priority: Uploaded File > Disk File
df_iss_raw = pd.read_csv(uploaded_iss, low_memory=False) if uploaded_iss else disk_iss
df_wt_raw = pd.read_csv(uploaded_wt) if uploaded_wt else disk_wt

if uploaded_sup:
    if uploaded_sup.name.endswith('.csv'):
        df_sup_raw = pd.read_csv(uploaded_sup, low_memory=False)
    else:
        df_sup_raw = pd.read_excel(uploaded_sup, sheet_name='공급_RAW')
else:
    df_sup_raw = disk_sup

# Header Notice
st.title("✈️ 항공사 노선별 M/S 대시보드")
st.markdown(f"""
<div class="source-header-box">
    <b>📌 출처: DDS & OAG 공급 데이터</b> &nbsp;|&nbsp; 
    <b>🗓️ 발매일:</b> {issue_range_str} &nbsp;|&nbsp; 
    <b>✈️ 출발일:</b> {dep_range_str}
</div>
""", unsafe_allow_html=True)

# Select Mode
dashboard_mode = st.radio(
    "📊 대시보드 분석 모드 선택:",
    options=["🎟️ 발매 M/S 대시보드", "✈️ 공급 M/S 대시보드"],
    horizontal=True
)

ALL_OPTION = "전체 (All)"

# ==========================================
# MODE 1: 발매 M/S 대시보드
# ==========================================
if dashboard_mode == "🎟️ 발매 M/S 대시보드":
    if df_iss_raw is None or df_wt_raw is None:
        st.info("👈 좌측 사이드바에서 [Ticketing-test_2.csv]와 [가중치 파일.csv]를 업로드해주세요.")
        st.stop()

    df = df_iss_raw.copy()
    df_wt = df_wt_raw.copy()

    df_wt['Weight_clean'] = df_wt['Weight'].astype(str).str.replace('%', '').str.strip()
    df_wt['Weight_num'] = pd.to_numeric(df_wt['Weight_clean'], errors='coerce') / 100.0
    df_wt_subset = df_wt[['Route Code', 'Dominant Marketing Airline', 'Weight_num']].dropna(subset=['Route Code', 'Dominant Marketing Airline'])

    merged_df = pd.merge(
        df, df_wt_subset,
        left_on=['노선', 'Dominant Marketing Airline'],
        right_on=['Route Code', 'Dominant Marketing Airline'],
        how='left'
    )
    merged_df['Weight_num'] = merged_df['Weight_num'].fillna(1.0)
    merged_df['Value'] = pd.to_numeric(merged_df['Value'], errors='coerce').fillna(0)
    merged_df['Weighted_Value'] = merged_df['Value'] * merged_df['Weight_num']

    route_order_list = merged_df.groupby('노선')['Weighted_Value'].sum().sort_values(ascending=False).index.tolist()
    all_dep_months = sorted([str(x) for x in merged_df['출발 월'].dropna().unique()])
    all_bounds = sorted([str(x) for x in merged_df['Bound'].dropna().unique()])
    all_ticket_types = sorted([str(x) for x in merged_df['Ticket Type'].dropna().unique()])
    all_channels = sorted([str(x) for x in merged_df['판매채널'].dropna().unique()])

    raw_airlines = sorted([str(x) for x in merged_df['Dominant Marketing Airline'].dropna().unique()])
    all_airlines = ['KE'] + [x for x in raw_airlines if x != 'KE'] if 'KE' in raw_airlines else raw_airlines

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 발매 대시보드 필터")
    with st.sidebar.form("iss_filter_form"):
        apply_weight_toggle = st.toggle("⚖️ 가중치 적용 M/S 산출", value=True)
        
        def get_form_selection(label, full_list):
            options = [ALL_OPTION] + full_list
            selected = st.multiselect(label, options=options, default=[ALL_OPTION])
            return full_list if ALL_OPTION in selected or not selected else selected

        selected_routes = get_form_selection("노선 (발매량 순)", route_order_list)
        selected_dep_months = get_form_selection("출발 월", all_dep_months)
        selected_bounds = get_form_selection("Bound", all_bounds)
        selected_ticket_types = get_form_selection("Ticket Type (여정)", all_ticket_types)
        selected_channels = get_form_selection("판매채널", all_channels)
        selected_airlines = get_form_selection("항공사 (KE 최우선)", all_airlines)

        st.form_submit_button("🚀 필터 적용하기", type="primary", use_container_width=True)

    val_col = 'Weighted_Value' if apply_weight_toggle else 'Value'

    filtered_df = merged_df[
        (merged_df['노선'].astype(str).isin(selected_routes)) &
        (merged_df['출발 월'].astype(str).isin(selected_dep_months)) &
        (merged_df['Bound'].astype(str).isin(selected_bounds)) &
        (merged_df['Ticket Type'].astype(str).isin(selected_ticket_types)) &
        (merged_df['판매채널'].astype(str).isin(selected_channels)) &
        (merged_df['Dominant Marketing Airline'].astype(str).isin(selected_airlines))
    ]

    color_discrete_map = {'KE': '#00A1E9'}

    # KPI Row
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    total_pax = filtered_df[val_col].sum()
    ke_pax = filtered_df[filtered_df['Dominant Marketing Airline'] == 'KE'][val_col].sum() if not filtered_df.empty else 0
    ke_ms = (ke_pax / total_pax * 100) if total_pax > 0 else 0

    top_al = "-"
    top_ms = 0.0
    if not filtered_df.empty and total_pax > 0:
        al_sum = filtered_df.groupby('Dominant Marketing Airline')[val_col].sum()
        top_al = al_sum.idxmax()
        top_ms = (al_sum.max() / total_pax) * 100

    top_route = filtered_df.groupby('노선')[val_col].sum().idxmax() if not filtered_df.empty else "-"
    status_wt_label = " (가중치 적용)" if apply_weight_toggle else " (순수 Raw)"

    with col_m1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">총 발매 실적{status_wt_label}</div><div class="metric-value">{total_pax:,.0f}</div></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="metric-card-ke"><div class="metric-title" style="color:#0284c7; font-weight:bold;">✈️ KE (대한항공) M/S</div><div class="metric-value" style="color:#0284c7;">{ke_pax:,.0f} ({ke_ms:.1f}%)</div></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">1위 항공사 (M/S)</div><div class="metric-value" style="color:#1d4ed8;"><b>{top_al}</b> ({top_ms:.1f}%)</div></div>', unsafe_allow_html=True)
    with col_m4:
        st.markdown(f'<div class="metric-card"><div class="metric-title">최대 실적 노선</div><div class="metric-value" style="color:#047857;">{top_route}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈 시각화 분석 차트", "📊 M/S 피벗 테이블", "📋 Raw Data View"])
    with tab1:
        st.subheader(f"📊 발매 M/S 시각화 분석{status_wt_label}")
        if not filtered_df.empty:
            al_order = [al for al in all_airlines if al in filtered_df['Dominant Marketing Airline'].unique()]
            c1, c2 = st.columns(2)
            with c1:
                pie_al = filtered_df.groupby('Dominant Marketing Airline')[val_col].sum().reset_index()
                fig1 = px.pie(pie_al, values=val_col, names='Dominant Marketing Airline', title='1. 항공사별 M/S 점유비 (KE 하늘색 강조)', hole=0.4, category_orders={'Dominant Marketing Airline': al_order}, color='Dominant Marketing Airline', color_discrete_map=color_discrete_map)
                fig1.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>항공사: %{label}</b><br>실적: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                df_w = filtered_df.groupby(['발매주차', 'Dominant Marketing Airline'])[val_col].sum().reset_index()
                fig2 = px.bar(df_w, x='발매주차', y=val_col, color='Dominant Marketing Airline', title='2. 주차별 항공사 실적 추이', barmode='stack', category_orders={'Dominant Marketing Airline': al_order}, color_discrete_map=color_discrete_map, text=val_col)
                fig2.update_traces(texttemplate='%{text:,.0f}', textposition='inside', hovertemplate="<b>주차: %{x}</b><br>항공사: %{fullData.name}<br>실적: %{y:,.0f}<extra></extra>")
                st.plotly_chart(fig2, use_container_width=True)
            st.markdown("---")
            c3, c4, c5 = st.columns(3)
            with c3:
                fig3 = px.pie(filtered_df.groupby('Bound')[val_col].sum().reset_index(), values=val_col, names='Bound', title='3. BOUND별 점유비', hole=0.4)
                st.plotly_chart(fig3, use_container_width=True)
            with c4:
                fig4 = px.pie(filtered_df.groupby('Ticket Type')[val_col].sum().reset_index(), values=val_col, names='Ticket Type', title='4. TRIP TYPE별 점유비', hole=0.4)
                st.plotly_chart(fig4, use_container_width=True)
            with c5:
                fig5 = px.pie(filtered_df.groupby('판매채널')[val_col].sum().reset_index(), values=val_col, names='판매채널', title='5. 판매 채널별 점유비', hole=0.4)
                st.plotly_chart(fig5, use_container_width=True)

    with tab2:
        st.markdown("##### 📌 주차별 및 노선별 발매 M/S 매트릭스")
        t1, t2 = st.columns([1.1, 1])
        with t1:
            piv_w = filtered_df.pivot_table(index='Dominant Marketing Airline', columns='발매주차', values=val_col, aggfunc='sum', fill_value=0)
            piv_w_ms = piv_w.divide(piv_w.sum(axis=0), axis=1) * 100
            al_sorted = ['KE'] + [x for x in piv_w_ms.index if x != 'KE'] if 'KE' in piv_w_ms.index else piv_w_ms.index
            st.dataframe(piv_w_ms.loc[al_sorted].applymap(lambda x: f"{x:.1f}%"), use_container_width=True)
        with t2:
            piv_r = filtered_df.pivot_table(index='노선', columns='Dominant Marketing Airline', values=val_col, aggfunc='sum', fill_value=0)
            cols_ke = ['KE'] + [x for x in piv_r.columns if x != 'KE'] if 'KE' in piv_r.columns else piv_r.columns
            piv_r_ms = piv_r[cols_ke].divide(piv_r.sum(axis=1), axis=0) * 100
            st.dataframe(piv_r_ms.applymap(lambda x: f"{x:.1f}%"), use_container_width=True)

    with tab3:
        st.dataframe(filtered_df, use_container_width=True)

# ==========================================
# MODE 2: 공급 M/S 대시보드
# ==========================================
else:
    if df_sup_raw is None:
        st.info("👈 좌측 사이드바에서 [공급 (9월 1주).csv] 파일을 업로드해주세요.")
        st.stop()

    df_sup = df_sup_raw.copy()
    df_sup.columns = [c.strip() for c in df_sup.columns]
    
    if 'Op Airline Code' in df_sup.columns:
        df_sup['Airline'] = df_sup['Op Airline Code']
    elif 'Mkt Al' in df_sup.columns:
        df_sup['Airline'] = df_sup['Mkt Al']
    else:
        df_sup['Airline'] = 'Unknown'

    if 'Seats' in df_sup.columns:
        df_sup['Seats_num'] = pd.to_numeric(df_sup['Seats'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    else:
        df_sup['Seats_num'] = 0

    if 'Flights' in df_sup.columns:
        df_sup['Flights_num'] = pd.to_numeric(df_sup['Flights'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    else:
        df_sup['Flights_num'] = 1

    sup_routes = df_sup.groupby('노선')['Seats_num'].sum().sort_values(ascending=False).index.tolist()
    sup_months = sorted([str(x) for x in df_sup['출발 월'].dropna().unique()]) if '출발 월' in df_sup.columns else []
    sup_time_cats = sorted([str(x) for x in df_sup['출발 시간대'].dropna().unique()]) if '출발 시간대' in df_sup.columns else []
    sup_ke_status = sorted([str(x) for x in df_sup['KE취항여부'].dropna().unique()]) if 'KE취항여부' in df_sup.columns else []
    
    raw_sup_al = sorted([str(x) for x in df_sup['Airline'].dropna().unique()])
    sup_airlines = ['KE'] + [x for x in raw_sup_al if x != 'KE'] if 'KE' in raw_sup_al else raw_sup_al

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 공급 대시보드 필터")
    with st.sidebar.form("sup_filter_form"):
        metric_mode = st.radio("📊 분석 공급 지표 선택:", options=["공급석 (Seats)", "운항 편수 (Flight Frequencies)"], horizontal=True)
        
        def get_sup_selection(label, full_list):
            options = [ALL_OPTION] + full_list
            selected = st.multiselect(label, options=options, default=[ALL_OPTION])
            return full_list if ALL_OPTION in selected or not selected else selected

        selected_sup_routes = get_sup_selection("노선 (공급석 순)", sup_routes)
        selected_sup_months = get_sup_selection("출발 월", sup_months)
        selected_sup_times = get_sup_selection("출발 시간대", sup_time_cats)
        selected_sup_ke_status = get_sup_selection("KE 취항여부", sup_ke_status)
        selected_sup_airlines = get_sup_selection("항공사 (KE 최우선)", sup_airlines)

        st.form_submit_button("🚀 공급 필터 적용하기", type="primary", use_container_width=True)

    target_val = 'Seats_num' if "공급석" in metric_mode else 'Flights_num'

    filter_mask = (
        (df_sup['노선'].astype(str).isin(selected_sup_routes)) &
        (df_sup['Airline'].astype(str).isin(selected_sup_airlines))
    )
    if '출발 월' in df_sup.columns:
        filter_mask &= (df_sup['출발 월'].astype(str).isin(selected_sup_months))
    if '출발 시간대' in df_sup.columns:
        filter_mask &= (df_sup['출발 시간대'].astype(str).isin(selected_sup_times))
    if 'KE취항여부' in df_sup.columns:
        filter_mask &= (df_sup['KE취항여부'].astype(str).isin(selected_sup_ke_status))

    filtered_sup = df_sup[filter_mask]

    color_discrete_map = {'KE': '#00A1E9'}

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    total_seats = filtered_sup['Seats_num'].sum()
    total_flights = filtered_sup['Flights_num'].sum()
    
    ke_sup_val = filtered_sup[filtered_sup['Airline'] == 'KE'][target_val].sum() if not filtered_sup.empty else 0
    total_sup_val = filtered_sup[target_val].sum()
    ke_sup_ms = (ke_sup_val / total_sup_val * 100) if total_sup_val > 0 else 0

    top_sup_al = filtered_sup.groupby('Airline')[target_val].sum().idxmax() if not filtered_sup.empty else "-"

    with col_s1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">총 공급 좌석수 (Seats)</div><div class="metric-value">{total_seats:,.0f}석</div></div>', unsafe_allow_html=True)
    with col_s2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">총 운항 편수 (Flights)</div><div class="metric-value">{total_flights:,.0f}회</div></div>', unsafe_allow_html=True)
    with col_s3:
        st.markdown(f'<div class="metric-card-ke"><div class="metric-title" style="color:#0284c7; font-weight:bold;">✈️ KE 공급 M/S ({metric_mode.split()[0]})</div><div class="metric-value" style="color:#0284c7;">{ke_sup_val:,.0f} ({ke_sup_ms:.1f}%)</div></div>', unsafe_allow_html=True)
    with col_s4:
        st.markdown(f'<div class="metric-card"><div class="metric-title">공급 M/S 1위 항공사</div><div class="metric-value" style="color:#1d4ed8;"><b>{top_sup_al}</b></div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_s1, tab_s2, tab_s3 = st.tabs(["📈 공급 시각화 분석 차트", "📊 공급 M/S 피벗 테이블", "📋 공급 Raw View"])

    with tab_s1:
        st.subheader(f"📊 항공사 / 노선별 공급 M/S 분석 ({metric_mode})")
        if not filtered_sup.empty:
            sup_al_order = [al for al in sup_airlines if al in filtered_sup['Airline'].unique()]
            
            cs1, cs2 = st.columns(2)
            with cs1:
                pie_sup_al = filtered_sup.groupby('Airline')[target_val].sum().reset_index()
                fig_s1 = px.pie(
                    pie_sup_al, values=target_val, names='Airline',
                    title='1. 항공사별 공급 M/S 점유비 (KE 하늘색 강조)', hole=0.4,
                    category_orders={'Airline': sup_al_order},
                    color='Airline', color_discrete_map=color_discrete_map
                )
                fig_s1.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>항공사: %{label}</b><br>공급량: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                st.plotly_chart(fig_s1, use_container_width=True)

            with cs2:
                bar_sup_route = filtered_sup.groupby(['노선', 'Airline'])[target_val].sum().reset_index()
                fig_s2 = px.bar(
                    bar_sup_route, x='노선', y=target_val, color='Airline',
                    title='2. 노선별 항공사 공급량 비교', barmode='stack',
                    category_orders={'Airline': sup_al_order},
                    color_discrete_map=color_discrete_map, text=target_val
                )
                fig_s2.update_traces(texttemplate='%{text:,.0f}', textposition='inside', hovertemplate="<b>노선: %{x}</b><br>항공사: %{fullData.name}<br>공급: %{y:,.0f}<extra></extra>")
                st.plotly_chart(fig_s2, use_container_width=True)

            st.markdown("---")
            cs3, cs4, cs5 = st.columns(3)
            with cs3:
                if '출발 시간대' in filtered_sup.columns:
                    fig_s3 = px.pie(filtered_sup.groupby('출발 시간대')[target_val].sum().reset_index(), values=target_val, names='출발 시간대', title='3. 출발 시간대별 공급 비중', hole=0.4)
                    st.plotly_chart(fig_s3, use_container_width=True)
            with cs4:
                if 'KE취항여부' in filtered_sup.columns:
                    fig_s4 = px.pie(filtered_sup.groupby('KE취항여부')[target_val].sum().reset_index(), values=target_val, names='KE취항여부', title='4. KE 취항여부별 공급 비중', hole=0.4)
                    st.plotly_chart(fig_s4, use_container_width=True)
            with cs5:
                if '출발 월' in filtered_sup.columns:
                    fig_s5 = px.pie(filtered_sup.groupby('출발 월')[target_val].sum().reset_index(), values=target_val, names='출발 월', title='5. 출발 월별 공급 분포', hole=0.4)
                    st.plotly_chart(fig_s5, use_container_width=True)

    with tab_s2:
        st.markdown(f"##### 📌 노선 및 출발월별 공급 M/S 매트릭스 ({metric_mode})")
        ts1, ts2 = st.columns([1.1, 1])
        with ts1:
            piv_s_route = filtered_sup.pivot_table(index='노선', columns='Airline', values=target_val, aggfunc='sum', fill_value=0)
            cols_sup_ke = ['KE'] + [x for x in piv_s_route.columns if x != 'KE'] if 'KE' in piv_s_route.columns else piv_s_route.columns
            piv_s_route = piv_s_route[cols_sup_ke]
            
            piv_s_route_ms = piv_s_route.divide(piv_s_route.sum(axis=1), axis=0) * 100
            st.dataframe(piv_s_route_ms.applymap(lambda x: f"{x:.1f}%" if pd.notnull(x) and x > 0 else "0.0%"), use_container_width=True)

        with ts2:
            if '출발 월' in filtered_sup.columns:
                piv_s_month = filtered_sup.pivot_table(index='Airline', columns='출발 월', values=target_val, aggfunc='sum', fill_value=0)
                piv_s_month_ms = piv_s_month.divide(piv_s_month.sum(axis=0), axis=1) * 100
                al_sup_ke = ['KE'] + [x for x in piv_s_month_ms.index if x != 'KE'] if 'KE' in piv_s_month_ms.index else piv_s_month_ms.index
                st.dataframe(piv_s_month_ms.loc[al_sup_ke].applymap(lambda x: f"{x:.1f}%" if pd.notnull(x) and x > 0 else "0.0%"), use_container_width=True)

    with tab_s3:
        st.dataframe(filtered_sup, use_container_width=True)