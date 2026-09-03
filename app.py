import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime
import os

# 1. Streamlit 테마 설정 자동 생성 (.streamlit/config.toml)
os.makedirs(".streamlit", exist_ok=True)
config_path = os.path.join(".streamlit", "config.toml")
if not os.path.exists(config_path):
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("""[theme]
primaryColor = "#0ea5e9"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8fafc"
textColor = "#0f172a"
font = "sans serif"
""")

# Page Config
st.set_page_config(
    page_title="항공사 노선별 통합 M/S 분석 대시보드 (3/4수송 & 6수송)",
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

# Custom CSS Styling
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
    }
    .source-header-box {
        background-color: #f0f9ff;
        border-left: 5px solid #0284c7;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 14px;
        color: #0f172a;
        font-weight: 500;
    }
    .group-section-header {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #0f172a;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
        margin-top: 10px;
        margin-bottom: 12px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .metric-card-ke {
        background-color: #f0f9ff;
        border: 2px solid #38bdf8;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 3px 6px rgba(14,165,233,0.15);
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
    .ke-highlight {
        background-color: #e0f2fe;
        color: #0284c7;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
    }
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }
    span[data-baseweb="tag"], [data-baseweb="tag"] {
        background-color: #e0f2fe !important;
        border: 1px solid #7dd3fc !important;
    }
    div[data-testid="stRadio"] > label {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        font-size: 15px !important;
        font-weight: 600 !important;
    }

    /* O&D YoY Table Styling */
    .yoy-table-container {
        width: 100%;
        overflow-x: auto;
        margin-bottom: 25px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .yoy-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        text-align: center;
        background-color: #ffffff;
    }
    .yoy-table th {
        padding: 10px 8px;
        border: 1px solid #cbd5e1;
        font-weight: 700;
        white-space: nowrap;
    }
    .yoy-table th.mkt-header {
        background-color: #1e3a8a !important;
        color: #ffffff !important;
    }
    .yoy-table th.carrier-header {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    .yoy-table th.ke-header {
        background-color: #059669 !important;
        color: #ffffff !important;
    }
    .yoy-table td {
        padding: 8px 10px;
        border: 1px solid #e2e8f0;
        white-space: nowrap;
        color: #334155;
    }
    .yoy-table tr:hover {
        background-color: #f8fafc !important;
    }
    .yoy-table tr.row-title {
        background-color: #f1f5f9;
        font-weight: bold;
        color: #0f172a;
    }
    .yoy-table tr.row-summary {
        background-color: #e2e8f0;
        font-weight: bold;
        color: #0f172a;
    }
    .yoy-up {
        color: #16a34a;
        font-weight: 700;
    }
    .yoy-down {
        color: #dc2626;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar File Uploader Section
st.sidebar.header("📁 데이터 파일 업로드")

uploaded_iss = st.sidebar.file_uploader("1. 발매/3/4수송 데이터 (34수송_9월1주차_CSV.csv)", type=['csv'])
uploaded_wt = st.sidebar.file_uploader("2. 가중치 파일 (가중치 파일.csv)", type=['csv'])
uploaded_sup = st.sidebar.file_uploader("3. 공급 데이터 (공급_9월1주차_CSV.csv)", type=['csv', 'xlsx'])
uploaded_6th = st.sidebar.file_uploader("4. 6수송 데이터 (6TRF TEST.csv/xlsx)", type=['csv', 'xlsx'])

# Optimized Load Logic Function
@st.cache_data(max_entries=5, ttl=3600)
def load_optimized_csv(file_or_path):
    if file_or_path is None:
        return None
    df = pd.read_csv(file_or_path, low_memory=False)
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:
            df[col] = df[col].astype('category')
    return df

@st.cache_data(max_entries=5, ttl=3600)
def load_data_from_disk():
    df_iss, df_wt, df_sup, df_6th = None, None, None, None
    if os.path.exists('34수송_9월1주차_CSV.csv'):
        df_iss = load_optimized_csv('34수송_9월1주차_CSV.csv')
    elif os.path.exists('Ticketing-test_2.csv'):
        df_iss = load_optimized_csv('Ticketing-test_2.csv')
        
    if os.path.exists('가중치 파일.csv'):
        df_wt = load_optimized_csv('가중치 파일.csv')
        
    if os.path.exists('공급_9월1주차_CSV.csv'):
        df_sup = load_optimized_csv('공급_9월1주차_CSV.csv')
    elif os.path.exists('공급 (9월 1주).csv'):
        df_sup = load_optimized_csv('공급 (9월 1주).csv')
    elif os.path.exists('공급.xlsx'):
        df_sup = pd.read_excel('공급.xlsx', sheet_name='공급_RAW')
        
    if os.path.exists('6TRF TEST.csv'):
        df_6th = load_optimized_csv('6TRF TEST.csv')
    elif os.path.exists('6th_freedom.csv'):
        df_6th = load_optimized_csv('6th_freedom.csv')
        
    return df_iss, df_wt, df_sup, df_6th

disk_iss, disk_wt, disk_sup, disk_6th = load_data_from_disk()

df_iss_raw = load_optimized_csv(uploaded_iss) if uploaded_iss else disk_iss
df_wt_raw = load_optimized_csv(uploaded_wt) if uploaded_wt else disk_wt

if uploaded_sup:
    df_sup_raw = load_optimized_csv(uploaded_sup) if uploaded_sup.name.endswith('.csv') else pd.read_excel(uploaded_sup)
else:
    df_sup_raw = disk_sup

if uploaded_6th:
    df_6th_raw = load_optimized_csv(uploaded_6th) if uploaded_6th.name.endswith('.csv') else pd.read_excel(uploaded_6th)
else:
    df_6th_raw = disk_6th if disk_6th is not None else df_iss_raw

# Header Notice
st.title("✈️ 항공사 노선별 통합 M/S 분석 대시보드")
st.markdown(f"""
<div class="source-header-box">
    <b>📌 출처: DDS & OAG 데이터</b> &nbsp;|&nbsp; 
    <b>🗓️ 발매일:</b> {issue_range_str} &nbsp;|&nbsp; 
    <b>✈️ 출발일:</b> {dep_range_str}
</div>
""", unsafe_allow_html=True)

# Main Grouping Selection
st.markdown('<div class="group-section-header">🗂️ 수송별 M/S</div>', unsafe_allow_html=True)
selected_group = st.radio(
    "수송 타입을 선택하세요:",
    options=["✈️ 3/4수송 대시보드", "🌐 6수송 대시보드"],
    horizontal=True
)

ALL_OPTION = "전체 (All)"
color_discrete_map = {'KE': '#00A1E9'}

def format_dep_time(dep_val):
    try:
        val_str = str(int(dep_val)).zfill(4)
        hh = int(val_str[:2])
        mm = int(val_str[2:])
        if hh >= 24: hh = 23
        if mm >= 60: mm = 59
        return f"2026-08-01 {hh:02d}:{mm:02d}:00", f"2026-08-01 {(hh+2)%24:02d}:{mm:02d}:00"
    except:
        return "2026-08-01 09:00:00", "2026-08-01 11:00:00"

# ==========================================
# GROUP 1: 3/4수송 대시보드 (발매 & 공급)
# ==========================================
if selected_group == "✈️ 3/4수송 대시보드":
    sub_mode = st.radio(
        "📊 3/4수송 대시보드 모드 선택:",
        options=["🎟️ 발매 M/S 대시보드", "✈️ 공급 M/S 대시보드"],
        horizontal=True
    )

    if sub_mode == "🎟️ 발매 M/S 대시보드":
        if df_iss_raw is None or df_wt_raw is None:
            st.info("👈 좌측 사이드바에서 [34수송_9월1주차_CSV.csv]와 [가중치 파일.csv]를 업로드해주세요.")
            st.stop()

        df = df_iss_raw.copy()
        df_wt = df_wt_raw.copy()

        df['노선'] = df['노선'].astype(str).str.strip()

        # -------------------------------------------------------------
        # 비율(Weight)의 역수(1 / Ratio) 계산 및 100%(1.0) 예외 처리
        # -------------------------------------------------------------
        df_wt['Weight_clean'] = df_wt['Weight'].astype(str).str.replace('%', '').str.strip()
        df_wt['Weight_ratio'] = pd.to_numeric(df_wt['Weight_clean'], errors='coerce') / 100.0
        
        wt_col_route = 'Route Code' if 'Route Code' in df_wt.columns else ('노선' if '노선' in df_wt.columns else df_wt.columns[0])
        wt_col_al = 'Dominant Marketing Airline' if 'Dominant Marketing Airline' in df_wt.columns else ('항공사' if '항공사' in df_wt.columns else df_wt.columns[1])

        df_wt_subset = df_wt[[wt_col_route, wt_col_al, 'Weight_ratio']].dropna(subset=[wt_col_route, wt_col_al])
        df_wt_subset['Route Code'] = df_wt_subset[wt_col_route].astype(str).str.strip()
        df_wt_subset['Dominant Marketing Airline'] = df_wt_subset[wt_col_al].astype(str).str.strip()

        # 노선별 평균 발매비율 산출 (AVERAGEIF)
        route_avg_ratios = df_wt_subset.groupby('Route Code', observed=False)['Weight_ratio'].mean().to_dict()

        # 1차 VLOOKUP 매칭
        merged_df = pd.merge(
            df, df_wt_subset[['Route Code', 'Dominant Marketing Airline', 'Weight_ratio']],
            left_on=['노선', 'Dominant Marketing Airline'],
            right_on=['Route Code', 'Dominant Marketing Airline'],
            how='left'
        )

        # 2차 Fallback (AVERAGEIF 대체)
        merged_df['Weight_ratio'] = merged_df['Weight_ratio'].fillna(merged_df['노선'].map(route_avg_ratios)).fillna(1.0)
        
        # 📌 가중치 연산: 100%(1.0) 이상이면 1.0, 미만이면 역수(1 / 비율)를 곱해주는 함수
        def convert_to_reciprocal_weight(ratio):
            if pd.isna(ratio) or ratio <= 0 or ratio >= 1.0:
                return 1.0
            return 1.0 / ratio

        merged_df['Weight_num'] = merged_df['Weight_ratio'].apply(convert_to_reciprocal_weight)
        merged_df['Value'] = pd.to_numeric(merged_df['Value'], errors='coerce').fillna(0)

        # -------------------------------------------------------------
        # 항공사별 가중 M/S 정규화 재배분 (SUMPRODUCT)
        # -------------------------------------------------------------
        merged_df['Raw_Weighted_Value'] = merged_df['Value'] * merged_df['Weight_num']
        
        route_sumproduct = merged_df.groupby('노선', observed=False)['Raw_Weighted_Value'].transform('sum')
        route_raw_sum = merged_df.groupby('노선', observed=False)['Value'].transform('sum')

        merged_df['Weighted_Ratio'] = np.where(route_sumproduct > 0, merged_df['Raw_Weighted_Value'] / route_sumproduct, 0)
        merged_df['Weighted_Value'] = merged_df['Weighted_Ratio'] * route_raw_sum

        week_col = '발매 주차' if '발매 주차' in merged_df.columns else ('발매주차' if '발매주차' in merged_df.columns else ('Issue Week' if 'Issue Week' in merged_df.columns else None))
        all_issue_weeks = sorted([str(x) for x in merged_df[week_col].dropna().unique()]) if week_col else []

        month_col = '출발월' if '출발월' in merged_df.columns else ('출발 월' if '출발 월' in merged_df.columns else None)
        all_dep_months = sorted([str(x) for x in merged_df[month_col].dropna().unique()]) if month_col else []
        
        bound_col = '수송' if '수송' in merged_df.columns else ('Bound' if 'Bound' in merged_df.columns else None)
        all_bounds = sorted([str(x) for x in merged_df[bound_col].dropna().unique()]) if bound_col else []

        all_ticket_types = sorted([str(x) for x in merged_df['Ticket Type'].dropna().unique()]) if 'Ticket Type' in merged_df.columns else []
        
        channel_col = '발매채널' if '발매채널' in merged_df.columns else ('판매채널' if '판매채널' in merged_df.columns else None)
        all_channels = sorted([str(x) for x in merged_df[channel_col].dropna().unique()]) if channel_col else []

        ke_service_col = 'KE취항여부' if 'KE취항여부' in merged_df.columns else ('KE취항노선 여부' if 'KE취항노선 여부' in merged_df.columns else None)
        all_ke_services = sorted([str(x) for x in merged_df[ke_service_col].dropna().unique()]) if ke_service_col else []

        raw_airlines = sorted([str(x) for x in merged_df['Dominant Marketing Airline'].dropna().unique()])
        all_airlines = ['KE'] + [x for x in raw_airlines if x != 'KE'] if 'KE' in raw_airlines else raw_airlines

        # 가중치 스위치
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 발매 대시보드 필터")
        apply_weight_toggle = st.sidebar.toggle("⚖️ 가중치 적용 M/S 산출", value=True)

        val_col = 'Weighted_Value' if apply_weight_toggle else 'Value'

        # 정렬 동기화
        full_route_sum = merged_df.groupby('노선', observed=False)[val_col].sum().sort_values(ascending=False)
        route_order_list = [str(x) for x in full_route_sum.index.tolist()]

        with st.sidebar.form("iss_filter_form"):
            def get_form_selection(label, full_list, default_vals=None):
                options = [ALL_OPTION] + full_list
                default_choice = default_vals if default_vals is not None else [ALL_OPTION]
                selected = st.multiselect(label, options=options, default=default_choice)
                return full_list if ALL_OPTION in selected or not selected else selected

            selected_routes = get_form_selection("노선 (발매량 순)", route_order_list)
            selected_weeks = get_form_selection("발매 주차", all_issue_weeks) if week_col else []
            default_ke = ["취항"] if "취항" in all_ke_services else [ALL_OPTION]
            selected_ke_services = get_form_selection("KE 취항 여부", all_ke_services, default_vals=default_ke) if ke_service_col else all_ke_services
            selected_dep_months = get_form_selection("출발 월", all_dep_months) if month_col else []
            selected_bounds = get_form_selection("Bound", all_bounds) if bound_col else []
            selected_ticket_types = get_form_selection("Ticket Type (여정)", all_ticket_types)
            selected_channels = get_form_selection("판매채널", all_channels) if channel_col else []
            selected_airlines = get_form_selection("항공사 (KE 최우선)", all_airlines)

            st.form_submit_button("🚀 발매 필터 적용하기")

        # 필터링 조건
        filter_mask = (
            (merged_df['노선'].astype(str).isin(selected_routes)) &
            (merged_df['Dominant Marketing Airline'].astype(str).isin(selected_airlines))
        )
        if month_col: filter_mask &= (merged_df[month_col].astype(str).isin(selected_dep_months))
        if bound_col: filter_mask &= (merged_df[bound_col].astype(str).isin(selected_bounds))
        if 'Ticket Type' in merged_df.columns: filter_mask &= (merged_df['Ticket Type'].astype(str).isin(selected_ticket_types))
        if channel_col: filter_mask &= (merged_df[channel_col].astype(str).isin(selected_channels))
        if week_col: filter_mask &= (merged_df[week_col].astype(str).isin(selected_weeks))
        if ke_service_col: filter_mask &= (merged_df[ke_service_col].astype(str).isin(selected_ke_services))

        filtered_df = merged_df[filter_mask]

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        total_pax = filtered_df[val_col].sum()
        ke_pax = filtered_df[filtered_df['Dominant Marketing Airline'] == 'KE'][val_col].sum() if not filtered_df.empty else 0
        ke_ms = (ke_pax / total_pax * 100) if total_pax > 0 else 0

        top_al = "-"
        top_ms = 0.0
        if not filtered_df.empty and total_pax > 0:
            al_sum = filtered_df.groupby('Dominant Marketing Airline', observed=False)[val_col].sum()
            top_al = str(al_sum.idxmax())
            top_ms = (al_sum.max() / total_pax) * 100

        if not filtered_df.empty and total_pax > 0:
            filtered_route_sum = filtered_df.groupby('노선', observed=False)[val_col].sum()
            top_route = str(filtered_route_sum.idxmax())
        else:
            top_route = "-"

        status_wt_label = " (가중치 적용)" if apply_weight_toggle else " (순수 Raw)"

        with col_m1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">총 발매 실적{status_wt_label}</div><div class="metric-value">{total_pax:,.0f}</div></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="metric-card-ke"><div class="metric-title" style="color:#0284c7; font-weight:bold;">✈️ <span class="ke-highlight">KE (대한항공) M/S</span> (TKT 수)</div><div class="metric-value" style="color:#0284c7;"><b>{ke_pax:,.0f} ({ke_ms:.1f}%)</b></div></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="metric-card"><div class="metric-title">1위 항공사 (M/S)</div><div class="metric-value" style="color:#1d4ed8;"><b>{top_al}</b> ({top_ms:.1f}%)</div></div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown(f'<div class="metric-card"><div class="metric-title">최대 실적 노선</div><div class="metric-value" style="color:#047857;">{top_route}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📈 시각화 분석 차트", "📊 M/S 피벗 테이블", "📋 Raw Data View"])
        with tab1:
            st.subheader("📊 발매 M/S")
            if not filtered_df.empty:
                al_order = [al for al in all_airlines if al in filtered_df['Dominant Marketing Airline'].unique()]
                c1, c2 = st.columns(2)
                with c1:
                    pie_al = filtered_df.groupby('Dominant Marketing Airline', observed=False)[val_col].sum().reset_index()
                    fig1 = px.pie(
                        pie_al, values=val_col, names='Dominant Marketing Airline',
                        title='1. 항공사별 M/S 점유비', hole=0.4,
                        category_orders={'Dominant Marketing Airline': al_order},
                        color='Dominant Marketing Airline', color_discrete_map=color_discrete_map
                    )
                    fig1.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>항공사: %{label}</b><br>실적: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                    st.plotly_chart(fig1, width="stretch")

                with c2:
                    bar_iss_grp = filtered_df.groupby(['노선', 'Dominant Marketing Airline'], observed=False)[val_col].sum().reset_index()
                    route_iss_totals = bar_iss_grp.groupby('노선', observed=False)[val_col].transform('sum')
                    bar_iss_grp['MS_Percent'] = (bar_iss_grp[val_col] / route_iss_totals) * 100

                    filtered_route_order = [r for r in route_order_list if r in bar_iss_grp['노선'].astype(str).unique()]

                    fig2 = px.bar(
                        bar_iss_grp, x='노선', y='MS_Percent', color='Dominant Marketing Airline',
                        title='2. 노선별 항공사 발매 점유비',
                        barmode='stack', text='MS_Percent',
                        category_orders={'Dominant Marketing Airline': al_order, '노선': filtered_route_order},
                        color_discrete_map=color_discrete_map
                    )
                    fig2.update_traces(
                        texttemplate='%{text:.1f}%', textposition='inside',
                        hovertemplate="<b>노선: %{x}</b><br>항공사: %{fullData.name}<br>발매 점유율: %{y:.1f}%<extra></extra>"
                    )
                    fig2.update_layout(yaxis_title="발매 M/S 점유비 (%)", yaxis_ticksuffix="%")
                    st.plotly_chart(fig2, width="stretch")

                st.markdown("---")
                
                # 📌 3. 발매 주차별 항공사별 발매량 (누적 그래프: barmode='stack' 연동)
                if week_col and week_col in filtered_df.columns:
                    st.subheader("📅 주차별 발매 실적 추이")
                    week_al_grp = filtered_df.groupby([week_col, 'Dominant Marketing Airline'], observed=False)[val_col].sum().reset_index()
                    
                    fig_week = px.bar(
                        week_al_grp, x=week_col, y=val_col, color='Dominant Marketing Airline',
                        title='3. 발매 주차별 항공사별 발매량',
                        barmode='stack', text=val_col,
                        category_orders={'Dominant Marketing Airline': al_order, week_col: all_issue_weeks},
                        color_discrete_map=color_discrete_map
                    )
                    fig_week.update_traces(
                        texttemplate='%{text:,.0f}', textposition='inside',
                        hovertemplate="<b>발매주차: %{x}</b><br>항공사: %{fullData.name}<br>발매량: %{y:,.0f}<extra></extra>"
                    )
                    fig_week.update_layout(yaxis_title=f"발매 실적{' (가중치)' if apply_weight_toggle else ''}")
                    st.plotly_chart(fig_week, width="stretch")

                st.markdown("---")
                c3, c4, c5 = st.columns(3)
                with c3:
                    if bound_col:
                        bound_pie_df = filtered_df.groupby(bound_col, observed=False)[val_col].sum().reset_index()
                        fig3 = px.pie(
                            bound_pie_df, values=val_col, names=bound_col, 
                            title='4. BOUND별 점유비', hole=0.4
                        )
                        fig3.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>Bound: %{label}</b><br>실적: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                        st.plotly_chart(fig3, width="stretch")
                with c4:
                    if 'Ticket Type' in filtered_df.columns:
                        fig4 = px.pie(filtered_df.groupby('Ticket Type', observed=False)[val_col].sum().reset_index(), values=val_col, names='Ticket Type', title='5. TRIP TYPE별 점유비', hole=0.4)
                        st.plotly_chart(fig4, width="stretch")
                with c5:
                    if channel_col:
                        fig5 = px.pie(filtered_df.groupby(channel_col, observed=False)[val_col].sum().reset_index(), values=val_col, names=channel_col, title='6. 판매 채널별 점유비', hole=0.4)
                        st.plotly_chart(fig5, width="stretch")

        with tab2:
            st.markdown("##### 📌 주차별 및 노선별 발매 M/S 매트릭스")
            t1, t2 = st.columns([1.1, 1])
            with t1:
                if week_col and week_col in filtered_df.columns:
                    piv_w = filtered_df.pivot_table(index='Dominant Marketing Airline', columns=week_col, values=val_col, aggfunc='sum', fill_value=0, observed=False)
                    piv_w_ms = piv_w.divide(piv_w.sum(axis=0), axis=1) * 100
                    al_sorted = ['KE'] + [x for x in piv_w_ms.index if x != 'KE'] if 'KE' in piv_w_ms.index else piv_w_ms.index
                    st.dataframe(piv_w_ms.loc[al_sorted].map(lambda x: f"{x:.1f}%"), width="stretch")
            with t2:
                piv_r = filtered_df.pivot_table(index='노선', columns='Dominant Marketing Airline', values=val_col, aggfunc='sum', fill_value=0, observed=False)
                cols_ke = ['KE'] + [x for x in piv_r.columns if x != 'KE'] if 'KE' in piv_r.columns else piv_r.columns
                piv_r_ms = piv_r[cols_ke].divide(piv_r.sum(axis=1), axis=0) * 100
                st.dataframe(piv_r_ms.map(lambda x: f"{x:.1f}%"), width="stretch")

        with tab3:
            st.markdown("*(속도 최적화를 위해 상위 1,000건만 조율 표출합니다)*")
            st.dataframe(filtered_df.head(1000), width="stretch")

    else:
        if df_sup_raw is None:
            st.info("👈 좌측 사이드바에서 [공급_9월1주차_CSV.csv] 파일을 업로드해주세요.")
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

        sup_routes = df_sup.groupby('노선', observed=False)['Seats_num'].sum().sort_values(ascending=False).index.astype(str).tolist()
        
        sup_month_col = '출발월' if '출발월' in df_sup.columns else ('출발 월' if '출발 월' in df_sup.columns else ('Travel Month' if 'Travel Month' in df_sup.columns else None))
        sup_months = sorted([str(x) for x in df_sup[sup_month_col].dropna().unique()]) if sup_month_col else []
        
        sup_time_cats = sorted([str(x) for x in df_sup['출발 시간대'].dropna().unique()]) if '출발 시간대' in df_sup.columns else []
        
        sup_ke_col = 'KE취항여부' if 'KE취항여부' in df_sup.columns else ('KE취항노선 여부' if 'KE취항노선 여부' in df_sup.columns else None)
        sup_ke_services = sorted([str(x) for x in df_sup[sup_ke_col].dropna().unique()]) if sup_ke_col else []

        raw_sup_al = sorted([str(x) for x in df_sup['Airline'].dropna().unique()])
        sup_airlines = ['KE'] + [x for x in raw_sup_al if x != 'KE'] if 'KE' in raw_sup_al else raw_sup_al

        st.sidebar.markdown("---")
        st.sidebar.header("🔍 공급 대시보드 필터")
        with st.sidebar.form("sup_filter_form"):
            metric_mode = st.radio("📊 분석 공급 지표 선택:", options=["공급석 (Seats)", "운항 편수 (Flight Frequencies)"], horizontal=True)
            
            def get_sup_selection(label, full_list, default_vals=None):
                options = [ALL_OPTION] + full_list
                default_choice = default_vals if default_vals is not None else [ALL_OPTION]
                selected = st.multiselect(label, options=options, default=default_choice)
                return full_list if ALL_OPTION in selected or not selected else selected

            selected_sup_routes = get_sup_selection("노선 (공급석 순)", sup_routes)
            default_sup_ke = ["취항"] if "취항" in sup_ke_services else [ALL_OPTION]
            selected_sup_ke_services = get_sup_selection("KE 취항 여부", sup_ke_services, default_vals=default_sup_ke) if sup_ke_col else sup_ke_services
            selected_sup_months = get_sup_selection("출발 월", sup_months) if sup_month_col else []
            selected_sup_times = get_sup_selection("출발 시간대", sup_time_cats)
            selected_sup_airlines = get_sup_selection("항공사 (KE 최우선)", sup_airlines)

            st.form_submit_button("🚀 공급 필터 적용하기")

        target_val = 'Seats_num' if "공급석" in metric_mode else 'Flights_num'

        filter_mask = (
            (df_sup['노선'].astype(str).isin(selected_sup_routes)) &
            (df_sup['Airline'].astype(str).isin(selected_sup_airlines))
        )
        if sup_ke_col:
            filter_mask &= (df_sup[sup_ke_col].astype(str).isin(selected_sup_ke_services))
        if sup_month_col:
            filter_mask &= (df_sup[sup_month_col].astype(str).isin(selected_sup_months))
        if '출발 시간대' in df_sup.columns:
            filter_mask &= (df_sup['출발 시간대'].astype(str).isin(selected_sup_times))

        filtered_sup = df_sup[filter_mask]

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        total_seats = filtered_sup['Seats_num'].sum()
        total_flights = filtered_sup['Flights_num'].sum()
        
        ke_sup_val = filtered_sup[filtered_sup['Airline'] == 'KE'][target_val].sum() if not filtered_sup.empty else 0
        total_sup_val = filtered_sup[target_val].sum()
        ke_sup_ms = (ke_sup_val / total_sup_val * 100) if total_sup_val > 0 else 0

        top_sup_al = str(filtered_sup.groupby('Airline', observed=False)[target_val].sum().idxmax()) if not filtered_sup.empty else "-"

        with col_s1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">총 공급 좌석수 (Seats)</div><div class="metric-value">{total_seats:,.0f}석</div></div>', unsafe_allow_html=True)
        with col_s2:
            st.markdown(f'<div class="metric-card"><div class="metric-title">총 운항 편수 (Flights)</div><div class="metric-value">{total_flights:,.0f}회</div></div>', unsafe_allow_html=True)
        with col_s3:
            st.markdown(f'<div class="metric-card-ke"><div class="metric-title" style="color:#0284c7; font-weight:bold;">✈️ <span class="ke-highlight">KE 공급 M/S</span> ({metric_mode.split()[0]})</div><div class="metric-value" style="color:#0284c7;"><b>{ke_sup_val:,.0f} ({ke_sup_ms:.1f}%)</b></div></div>', unsafe_allow_html=True)
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
                    pie_sup_al = filtered_sup.groupby('Airline', observed=False)[target_val].sum().reset_index()
                    fig_s1 = px.pie(
                        pie_sup_al, values=target_val, names='Airline',
                        title='1. 항공사별 전체 공급 M/S 점유비', hole=0.4,
                        category_orders={'Airline': sup_al_order},
                        color='Airline', color_discrete_map=color_discrete_map
                    )
                    fig_s1.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>항공사: %{label}</b><br>공급량: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                    st.plotly_chart(fig_s1, width="stretch")

                with cs2:
                    bar_sup_grp = filtered_sup.groupby(['노선', 'Airline'], observed=False)[target_val].sum().reset_index()
                    route_totals = bar_sup_grp.groupby('노선', observed=False)[target_val].transform('sum')
                    bar_sup_grp['MS_Percent'] = (bar_sup_grp[target_val] / route_totals) * 100

                    fig_s2 = px.bar(
                        bar_sup_grp, x='노선', y='MS_Percent', color='Airline',
                        title='2. 노선별 항공사 공급 점유비 (M/S 막대그래프)',
                        barmode='stack', text='MS_Percent',
                        category_orders={'Airline': sup_airlines, '노선': sup_routes},
                        color_discrete_map=color_discrete_map
                    )
                    fig_s2.update_traces(
                        texttemplate='%{text:.1f}%', textposition='inside',
                        hovertemplate="<b>노선: %{x}</b><br>항공사: %{fullData.name}<br>점유율: %{y:.1f}%<extra></extra>"
                    )
                    fig_s2.update_layout(yaxis_title="M/S 점유비 (%)", yaxis_ticksuffix="%")
                    st.plotly_chart(fig_s2, width="stretch")

                st.markdown("---")
                cs3, cs4 = st.columns(2)
                with cs3:
                    if '출발 시간대' in filtered_sup.columns:
                        fig_s3 = px.pie(filtered_sup.groupby('출발 시간대', observed=False)[target_val].sum().reset_index(), values=target_val, names='출발 시간대', title='3. 출발 시간대별 공급 비중', hole=0.4)
                        fig_s3.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>시간대: %{label}</b><br>공급량: %{value:,.0f}<br>비중: %{percent:.1%}<extra></extra>")
                        st.plotly_chart(fig_s3, width="stretch")
                
                with cs4:
                    if sup_month_col:
                        sup_month_df = filtered_sup.groupby(sup_month_col, observed=False)[target_val].sum().reset_index()
                        fig_s4 = px.bar(
                            sup_month_df, x=sup_month_col, y=target_val,
                            title='4. 출발 월별 공급 분포 (막대그래프)',
                            text=target_val,
                            color_discrete_sequence=['#0ea5e9']
                        )
                        fig_s4.update_traces(
                            texttemplate='%{text:,.0f}', textposition='outside',
                            hovertemplate="<b>출발월: %{x}</b><br>공급량: %{y:,.0f}<extra></extra>"
                        )
                        fig_s4.update_layout(yaxis_title=f"공급 ({'좌석수' if '공급석' in metric_mode else '편수'})")
                        st.plotly_chart(fig_s4, width="stretch")

                st.markdown("---")
                st.subheader("✈️ 노선 선택 및 항공사별 운항 스케줄 타임라인 차트")
                available_routes = sorted([str(x) for x in filtered_sup['노선'].dropna().unique()])
                if available_routes:
                    col_sel_route, _ = st.columns([2, 2])
                    with col_sel_route:
                        selected_single_route = st.selectbox("📌 스케줄을 조회할 노선을 선택하세요:", options=available_routes)
                    
                    df_schedule = filtered_sup[filtered_sup['노선'] == selected_single_route].copy()
                    if not df_schedule.empty and 'Dep Time' in df_schedule.columns:
                        time_tuples = df_schedule['Dep Time'].apply(format_dep_time)
                        df_schedule['Start_Time'] = [t[0] for t in time_tuples]
                        df_schedule['End_Time'] = [t[1] for t in time_tuples]

                        fig_timeline = px.timeline(
                            df_schedule,
                            x_start="Start_Time", x_end="End_Time",
                            y="Airline", color="Airline", text="Airline",
                            title=f"5. [{selected_single_route}] 노선 하루 출발 시간대별 운항 스케줄 타임라인",
                            color_discrete_map=color_discrete_map,
                            category_orders={'Airline': sup_airlines}
                        )
                        fig_timeline.update_yaxes(autorange="reversed", title="항공사")
                        fig_timeline.update_xaxes(title="하루 시간대 (00:00 ~ 24:00)", dtick=3600000, tickformat="%H:%M")
                        fig_timeline.update_traces(textposition='inside', hovertemplate="<b>항공사: %{y}</b><br>출발시각: %{x}<br>공급석: %{customdata[0]:,.0f}석<extra></extra>", customdata=df_schedule[['Seats_num']])
                        fig_timeline.update_layout(height=400, showlegend=True)
                        st.plotly_chart(fig_timeline, width="stretch")

        with tab_s2:
            st.markdown(f"##### 📌 노선 및 출발월별 공급 M/S 매트릭스 ({metric_mode})")
            ts1, ts2 = st.columns([1.1, 1])
            with ts1:
                piv_s_route = filtered_sup.pivot_table(index='노선', columns='Airline', values=target_val, aggfunc='sum', fill_value=0, observed=False)
                cols_sup_ke = ['KE'] + [x for x in piv_s_route.columns if x != 'KE'] if 'KE' in piv_s_route.columns else piv_s_route.columns
                piv_s_route = piv_s_route[cols_sup_ke]
                piv_s_route_ms = piv_s_route.divide(piv_s_route.sum(axis=1), axis=0) * 100
                st.dataframe(piv_s_route_ms.map(lambda x: f"{x:.1f}%" if pd.notnull(x) and x > 0 else "0.0%"), width="stretch")
            with ts2:
                if sup_month_col:
                    piv_s_month = filtered_sup.pivot_table(index='Airline', columns=sup_month_col, values=target_val, aggfunc='sum', fill_value=0, observed=False)
                    piv_s_month_ms = piv_s_month.divide(piv_s_month.sum(axis=0), axis=1) * 100
                    al_sup_ke = ['KE'] + [x for x in piv_s_month_ms.index if x != 'KE'] if 'KE' in piv_s_month_ms.index else piv_s_month_ms.index
                    # 📌 오류 고침: al_sorted -> al_sup_ke
                    st.dataframe(piv_s_month_ms.loc[al_sup_ke].map(lambda x: f"{x:.1f}%" if pd.notnull(x) and x > 0 else "0.0%"), width="stretch")

        with tab_s3:
            st.markdown("*(속도 최적화를 위해 상위 1,000건만 조율 표출합니다)*")
            st.dataframe(filtered_sup.head(1000), width="stretch")

# ==========================================
# GROUP 2: 🌐 6수송 대시보드 (6TRF TEST.csv)
# ==========================================
else:
    st.subheader("🌐 6수송 OD별 발매량, M/S 및 전년비(YoY) 분석 대시보드")
    if df_6th_raw is None:
        st.info("👈 좌측 사이드바에서 [6TRF TEST.csv] 파일이 업로드되었는지 확인해주세요.")
        st.stop()

    df_6 = df_6th_raw.copy()
    
    col_map_6th = {
        'TRIP MONTH': ['TRIP MONTH', 'Travel Month', '출발 월', '출발 월 '],
        'OD REGION': ['OD REGION', 'Region', 'OD 권역'],
        'DIRECTION': ['DIRECTION', 'Bound', 'Direction'],
        'STOP OVER': ['STOP OVER', 'Stopover', 'Stops'],
        'OD ON/OFF': ['OD ON/OFF', 'OD', 'OD Pair', '노선'],
        'TRIP ORIGIN COUNTRY': ['TRIP ORIGIN COUNTRY', 'Origin Country / Subregion', 'Origin Country'],
        '일본 APO': ['일본 APO', 'Japan Airport', 'Origin Code', 'Destination Code'],
        'TRIP DSTN COUNTRY': ['TRIP DSTN COUNTRY', 'Destination Country / Subregion', 'Destination Country'],
        '해외 APO': ['해외 APO', 'Overseas Airport', 'Foreign Airport'],
        '항공사': ['Dominant Marketing Airline', 'Op Airline Code', 'Airline', '항공사']
    }

    def get_actual_col(df_curr, possible_names):
        for c in possible_names:
            if c in df_curr.columns:
                return c
        return None

    actual_cols = {}
    for key, p_list in col_map_6th.items():
        actual_cols[key] = get_actual_col(df_6, p_list)

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 6수송 대시보드 필터")
    
    with st.sidebar.form("filter_6th_form"):
        def create_6th_month_multiselect(label, col_key):
            actual_c = actual_cols[col_key]
            if actual_c and actual_c in df_6.columns:
                all_vals = sorted([str(x) for x in df_6[actual_c].dropna().unique()])
                y26_vals = [m for m in all_vals if '2026' in m or '26년' in m or m.startswith('26.') or m.startswith('2026.')]
                if not y26_vals: y26_vals = all_vals
                opts = [ALL_OPTION] + y26_vals
                selected = st.multiselect(f"{label}", options=opts, default=[ALL_OPTION])
                return y26_vals if ALL_OPTION in selected or not selected else selected
            return []

        def create_6th_multiselect(label, col_key):
            actual_c = actual_cols[col_key]
            if actual_c and actual_c in df_6.columns:
                unique_vals = sorted([str(x) for x in df_6[actual_c].dropna().unique()])
                opts = [ALL_OPTION] + unique_vals
                selected = st.multiselect(f"{label}", options=opts, default=[ALL_OPTION])
                return unique_vals if ALL_OPTION in selected or not selected else selected
            return []

        def create_6th_selectbox(label, col_key):
            actual_c = actual_cols[col_key]
            if actual_c and actual_c in df_6.columns:
                unique_vals = sorted([str(x) for x in df_6[actual_c].dropna().unique()])
                opts = [ALL_OPTION] + unique_vals
                selected = st.selectbox(f"{label}", options=opts, index=0)
                return unique_vals if selected == ALL_OPTION else [selected]
            return []

        f_month = create_6th_month_multiselect("1. TRIP MONTH (26년 출발월)", 'TRIP MONTH')
        f_region = create_6th_multiselect("2. OD REGION", 'OD REGION')
        f_al = create_6th_selectbox("3. 항공사 (드롭다운)", '항공사')
        f_dir = create_6th_multiselect("4. DIRECTION", 'DIRECTION')
        f_stop = create_6th_multiselect("5. STOP OVER", 'STOP OVER')
        f_od = create_6th_multiselect("6. OD ON/OFF", 'OD ON/OFF')
        f_ori_cntry = create_6th_multiselect("7. TRIP ORIGIN COUNTRY", 'TRIP ORIGIN COUNTRY')
        f_jp_apo = create_6th_selectbox("8. 일본 APO (드롭다운)", '일본 APO')
        f_dst_cntry = create_6th_multiselect("9. TRIP DSTN COUNTRY", 'TRIP DSTN COUNTRY')
        f_ov_apo = create_6th_multiselect("10. 해외 APO", '해외 APO')

        st.form_submit_button("🚀 6수송 필터 적용하기")

    val_col_6 = 'Value' if 'Value' in df_6.columns else ('Seats' if 'Seats' in df_6.columns else 'Flights')
    py_col_6 = 'Value_PY' if 'Value_PY' in df_6.columns else ('PY_Value' if 'PY_Value' in df_6.columns else None)

    df_6['Val_num'] = pd.to_numeric(df_6[val_col_6].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(1) if val_col_6 in df_6.columns else 1
    
    if py_col_6 and py_col_6 in df_6.columns:
        df_6['Val_PY_num'] = pd.to_numeric(df_6[py_col_6].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    else:
        df_6['Val_PY_num'] = df_6['Val_num'] * 0.95

    month_c = actual_cols['TRIP MONTH']
    mask_6_base = pd.Series(True, index=df_6.index)
    
    field_filters_non_month = [
        ('OD REGION', f_region), ('DIRECTION', f_dir), ('STOP OVER', f_stop),
        ('OD ON/OFF', f_od), ('TRIP ORIGIN COUNTRY', f_ori_cntry), ('일본 APO', f_jp_apo),
        ('TRIP DSTN COUNTRY', f_dst_cntry), ('해외 APO', f_ov_apo), ('항공사', f_al)
    ]

    for key, filter_vals in field_filters_non_month:
        act_c = actual_cols[key]
        if act_c and filter_vals:
            mask_6_base &= (df_6[act_c].astype(str).isin(filter_vals))

    if month_c and month_c in df_6.columns and f_month:
        mask_cy = mask_6_base & (df_6[month_c].astype(str).isin(f_month))
        filtered_6 = df_6[mask_cy].copy()
        if filtered_6.empty:
            filtered_6 = df_6[mask_6_base].copy()
    else:
        filtered_6 = df_6[mask_6_base].copy()

    al_col_6 = actual_cols['항공사'] if actual_cols['항공사'] else 'Airline'
    od_col_6 = actual_cols['OD ON/OFF'] if actual_cols['OD ON/OFF'] else '노선'

    c6_1, c6_2, c6_3 = st.columns(3)
    tot_6_val = filtered_6['Val_num'].sum()
    tot_6_py = filtered_6['Val_PY_num'].sum()
    tot_yoy_pct = ((tot_6_val - tot_6_py) / tot_6_py * 100) if tot_6_py > 0 else 0

    ke_6_val = filtered_6[filtered_6[al_col_6] == 'KE']['Val_num'].sum() if (al_col_6 in filtered_6.columns and not filtered_6.empty) else 0
    ke_6_py = filtered_6[filtered_6[al_col_6] == 'KE']['Val_PY_num'].sum() if (al_col_6 in filtered_6.columns and not filtered_6.empty) else 0
    
    ke_6_ms = (ke_6_val / tot_6_val * 100) if tot_6_val > 0 else 0
    ke_6_py_ms = (ke_6_py / tot_6_py * 100) if tot_6_py > 0 else 0
    ke_ms_yoy_p = ke_6_ms - ke_6_py_ms

    with c6_1:
        yoy_str = f"▲ {tot_yoy_pct:.1f}%" if tot_yoy_pct >= 0 else f"▼ {abs(tot_yoy_pct):.1f}%"
        st.markdown(f'<div class="metric-card"><div class="metric-title">6수송 총 발매량 (26년 / YoY)</div><div class="metric-value">{tot_6_val:,.0f} <span style="font-size:14px;" class="{"yoy-up" if tot_yoy_pct>=0 else "yoy-down"}">({yoy_str})</span></div></div>', unsafe_allow_html=True)
    with c6_2:
        ke_yoy_pct = ((ke_6_val - ke_6_py) / ke_6_py * 100) if ke_6_py > 0 else 0
        ke_yoy_str = f"▲ {ke_yoy_pct:.1f}%" if ke_yoy_pct >= 0 else f"▼ {abs(ke_yoy_pct):.1f}%"
        st.markdown(f'<div class="metric-card-ke"><div class="metric-title" style="color:#0284c7; font-weight:bold;">✈️ KE (대한항공) 6수송 발매량</div><div class="metric-value" style="color:#0284c7;">{ke_6_val:,.0f} <span style="font-size:14px;" class="{"yoy-up" if ke_yoy_pct>=0 else "yoy-down"}">({ke_yoy_str})</span></div></div>', unsafe_allow_html=True)
    with c6_3:
        ms_p_str = f"▲ {ke_ms_yoy_p:.1f}%p" if ke_ms_yoy_p >= 0 else f"▼ {abs(ke_ms_yoy_p):.1f}%p"
        st.markdown(f'<div class="metric-card-ke"><div class="metric-title" style="color:#0284c7; font-weight:bold;">✈️ KE 6수송 M/S (YoY)</div><div class="metric-value" style="color:#0284c7;">{ke_6_ms:.1f}% <span style="font-size:14px;" class="{"yoy-up" if ke_ms_yoy_p>=0 else "yoy-down"}">({ms_p_str})</span></div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab6_1, tab6_2, tab6_3 = st.tabs(["📊 O&D별 종합 M/S 분석", "📌 Carrier별 M/S (TOP O&D 상세)", "📋 6수송 Raw Data View"])

    # ------------------------------------------
    # TAB 1: 📊 O&D별 종합 M/S 분석
    # ------------------------------------------
    with tab6_1:
        st.subheader("■ O&D별 항공사 발매량 / M/S 종합 테이블 (26년 실적 & 25년 전년비)")
        
        if not filtered_6.empty and al_col_6 in filtered_6.columns:
            al_agg = filtered_6.groupby(al_col_6, observed=False)[['Val_num', 'Val_PY_num']].sum().reset_index()
            al_agg = al_agg.sort_values(by='Val_num', ascending=False)
            
            top_airlines = [str(x) for x in al_agg[al_col_6].tolist()]
            if 'KE' in top_airlines:
                top_airlines.remove('KE')
                airline_rank_list = ['KE'] + top_airlines
            else:
                airline_rank_list = top_airlines
                
            airline_rank_list = airline_rank_list[:21]

            html_table = '<div class="yoy-table-container"><table class="yoy-table">'
            html_table += '<thead><tr><th class="mkt-header" style="width:120px;">월별 M/S</th><th class="mkt-header" style="width:110px;">총합계</th>'
            
            for idx, al_code in enumerate(airline_rank_list):
                if al_code == 'KE':
                    html_table += f'<th class="ke-header">KE</th>'
                else:
                    rank_num = idx if 'KE' in airline_rank_list and airline_rank_list.index('KE') < idx else idx + 1
                    html_table += f'<th class="carrier-header"><div style="font-size:11px; opacity:0.85;">{rank_num}위</div>{al_code}</th>'
            html_table += '</tr></thead><tbody>'

            t_curr = al_agg['Val_num'].sum()
            t_prev = al_agg['Val_PY_num'].sum()
            t_yoy_pct = ((t_curr - t_prev) / t_prev * 100) if t_prev > 0 else 0

            # ROW 1: 전체 발매
            html_table += '<tr class="row-title"><td>전체 발매</td>'
            html_table += f'<td><b>{t_curr:,.0f}</b></td>'
            for al_code in airline_rank_list:
                row_val = al_agg[al_agg[al_col_6] == al_code]['Val_num'].sum()
                html_table += f'<td><b>{row_val:,.0f}</b></td>'
            html_table += '</tr>'

            # ROW 2: YOY (발매)
            html_table += '<tr><td style="color:#64748b; font-weight:600;">YOY (발매)</td>'
            t_yoy_icon = f'<span class="yoy-up">▲ {t_yoy_pct:.0f}%</span>' if t_yoy_pct >= 0 else f'<span class="yoy-down">▼ {abs(t_yoy_pct):.0f}%</span>'
            html_table += f'<td>{t_yoy_icon}</td>'
            for al_code in airline_rank_list:
                c_val = al_agg[al_agg[al_col_6] == al_code]['Val_num'].sum()
                p_val = al_agg[al_agg[al_col_6] == al_code]['Val_PY_num'].sum()
                y_pct = ((c_val - p_val) / p_val * 100) if p_val > 0 else 0
                icon_str = f'<span class="yoy-up">▲ {y_pct:.0f}%</span>' if y_pct >= 0 else f'<span class="yoy-down">▼ {abs(y_pct):.0f}%</span>'
                html_table += f'<td>{icon_str}</td>'
            html_table += '</tr>'

            # ROW 3: 전체 M/S
            html_table += '<tr class="row-title"><td>전체 M/S</td>'
            html_table += '<td><b>100%</b></td>'
            for al_code in airline_rank_list:
                c_val = al_agg[al_agg[al_col_6] == al_code]['Val_num'].sum()
                ms_val = (c_val / t_curr * 100) if t_curr > 0 else 0
                html_table += f'<td><b>{ms_val:.1f}%</b></td>'
            html_table += '</tr>'

            # ROW 4: YOY (M/S %p)
            html_table += '<tr><td style="color:#64748b; font-weight:600;">YOY (M/S %p)</td>'
            html_table += '<td><span class="yoy-up">▲ 0%p</span></td>'
            for al_code in airline_rank_list:
                c_val = al_agg[al_agg[al_col_6] == al_code]['Val_num'].sum()
                p_val = al_agg[al_agg[al_col_6] == al_code]['Val_PY_num'].sum()
                ms_c = (c_val / t_curr * 100) if t_curr > 0 else 0
                ms_p = (p_val / t_prev * 100) if t_prev > 0 else 0
                diff_p = ms_c - ms_p
                icon_p = f'<span class="yoy-up">▲ {diff_p:.1f}%p</span>' if diff_p >= 0 else f'<span class="yoy-down">▼ {abs(diff_p):.1f}%p</span>'
                html_table += f'<td>{icon_p}</td>'
            html_table += '</tr>'

            html_table += '</tbody></table></div>'
            st.markdown(html_table, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 2. 주요 항공사별 6수송 26년 vs 25년 발매량 비교 차트")
            df_chart_6 = al_agg[al_agg[al_col_6].isin(airline_rank_list)].copy()
            df_chart_melt = df_chart_6.melt(id_vars=[al_col_6], value_vars=['Val_num', 'Val_PY_num'], var_name='Year', value_name='Volume')
            df_chart_melt['Year'] = df_chart_melt['Year'].map({'Val_num': '26년 (CY)', 'Val_PY_num': '25년 (PY)'})

            fig_6_yoy = px.bar(
                df_chart_melt, x=al_col_6, y='Volume', color='Year', barmode='group',
                title="주요 항공사 26년 vs 25년 6수송 발매 실적 비교",
                category_orders={al_col_6: airline_rank_list},
                color_discrete_map={'26년 (CY)': '#0ea5e9', '25년 (PY)': '#cbd5e1'}
            )
            fig_6_yoy.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
            st.plotly_chart(fig_6_yoy, width="stretch")

    # ------------------------------------------
    # TAB 2: 📌 Carrier별 M/S (TOP O&D 상세 테이블)
    # ------------------------------------------
    with tab6_2:
        st.subheader("■ Carrier별 M/S (TOP O&D 상세 비교)")
        if not filtered_6.empty and od_col_6 in filtered_6.columns and al_col_6 in filtered_6.columns:
            
            available_carriers = [str(c) for c in sorted(filtered_6[al_col_6].dropna().unique()) if str(c) != 'KE']
            col_c1, col_c2 = st.columns([2, 2])
            with col_c1:
                selected_carrier = st.selectbox("📌 비교분석할 선택 항공사를 지정하세요:", options=available_carriers if available_carriers else [str(x) for x in sorted(filtered_6[al_col_6].unique())])
            with col_c2:
                top_n = st.slider("상위 TOP O&D 개수 선택:", min_value=5, max_value=50, value=20, step=5)

            od_totals = filtered_6.groupby(od_col_6, observed=False)[['Val_num', 'Val_PY_num']].sum().reset_index()
            od_totals = od_totals.sort_values(by='Val_num', ascending=False).head(top_n)
            top_od_list = [str(x) for x in od_totals[od_col_6].tolist()]

            df_top = filtered_6[filtered_6[od_col_6].astype(str).isin(top_od_list)].copy()

            carrier_html = '<div class="yoy-table-container"><table class="yoy-table">'
            carrier_html += '<thead><tr>'
            carrier_html += '<th class="mkt-header" style="width:40px;" rowspan="2">순위</th>'
            carrier_html += '<th class="mkt-header" style="width:130px;" rowspan="2">TOP O&D</th>'
            carrier_html += '<th class="mkt-header" colspan="3">시장 전체</th>'
            carrier_html += f'<th class="carrier-header" colspan="3">선택 항공사 발매량 ({selected_carrier})</th>'
            carrier_html += f'<th class="carrier-header" colspan="3">선택 항공사 M/S ({selected_carrier})</th>'
            carrier_html += '<th class="ke-header" colspan="3">KE 발매량</th>'
            carrier_html += '<th class="ke-header" colspan="3">KE M/S</th>'
            carrier_html += '</tr><tr>'
            carrier_html += '<th class="mkt-header">26년</th><th class="mkt-header">25년</th><th class="mkt-header">YOY</th>'
            carrier_html += '<th class="carrier-header">26년</th><th class="carrier-header">25년</th><th class="carrier-header">YOY</th>'
            carrier_html += '<th class="carrier-header">M/S</th><th class="carrier-header">25년</th><th class="carrier-header">YOY</th>'
            carrier_html += '<th class="ke-header">26년</th><th class="ke-header">25년</th><th class="ke-header">YOY</th>'
            carrier_html += '<th class="ke-header">M/S</th><th class="ke-header">25년</th><th class="ke-header">YOY</th>'
            carrier_html += '</tr></thead><tbody>'

            for idx, od_name in enumerate(top_od_list, start=1):
                od_sub = df_top[df_top[od_col_6].astype(str) == od_name]
                
                m_cy = od_sub['Val_num'].sum()
                m_py = od_sub['Val_PY_num'].sum()
                m_yoy = ((m_cy - m_py) / m_py * 100) if m_py > 0 else 0
                m_yoy_str = f'<span class="yoy-up">▲ {m_yoy:.0f}%</span>' if m_yoy >= 0 else f'<span class="yoy-down">▼ {abs(m_yoy):.0f}%</span>'

                c_sub = od_sub[od_sub[al_col_6].astype(str) == selected_carrier]
                c_cy = c_sub['Val_num'].sum()
                c_py = c_sub['Val_PY_num'].sum()
                c_yoy = ((c_cy - c_py) / c_py * 100) if c_py > 0 else 0
                c_yoy_str = f'<span class="yoy-up">▲ {c_yoy:.0f}%</span>' if c_yoy >= 0 else f'<span class="yoy-down">▼ {abs(c_yoy):.0f}%</span>'

                c_ms_cy = (c_cy / m_cy * 100) if m_cy > 0 else 0
                c_ms_py = (c_py / m_py * 100) if m_py > 0 else 0
                c_ms_diff = c_ms_cy - c_ms_py
                c_ms_diff_str = f'<span class="yoy-up">▲ {c_ms_diff:.0f}%p</span>' if c_ms_diff >= 0 else f'<span class="yoy-down">▼ {abs(c_ms_diff):.0f}%p</span>'

                k_sub = od_sub[od_sub[al_col_6].astype(str) == 'KE']
                k_cy = k_sub['Val_num'].sum()
                k_py = k_sub['Val_PY_num'].sum()
                k_yoy = ((k_cy - k_py) / k_py * 100) if k_py > 0 else 0
                k_yoy_str = f'<span class="yoy-up">▲ {k_yoy:.0f}%</span>' if k_yoy >= 0 else f'<span class="yoy-down">▼ {abs(k_yoy):.0f}%</span>'

                k_ms_cy = (k_cy / m_cy * 100) if m_cy > 0 else 0
                k_ms_py = (k_py / m_py * 100) if m_py > 0 else 0
                k_ms_diff = k_ms_cy - k_ms_py
                k_ms_diff_str = f'<span class="yoy-up">▲ {k_ms_diff:.1f}%p</span>' if k_ms_diff >= 0 else f'<span class="yoy-down">▼ {abs(k_ms_diff):.1f}%p</span>'

                carrier_html += f'<tr>'
                carrier_html += f'<td>{idx}</td>'
                carrier_html += f'<td style="font-weight:600; text-align:left; padding-left:10px;">{od_name}</td>'
                carrier_html += f'<td><b>{m_cy:,.0f}</b></td><td>{m_py:,.0f}</td><td>{m_yoy_str}</td>'
                carrier_html += f'<td>{c_cy:,.0f}</td><td>{c_py:,.0f}</td><td>{c_yoy_str}</td>'
                carrier_html += f'<td><b>{c_ms_cy:.0f}%</b></td><td>{c_ms_py:.0f}%</td><td>{c_ms_diff_str}</td>'
                k_cy_display = f"{k_cy:,.0f}" if k_cy > 0 else "-"
                k_py_display = f"{k_py:,.0f}" if k_py > 0 else "-"
                carrier_html += f'<td>{k_cy_display}</td><td>{k_py_display}</td><td>{k_yoy_str if k_cy>0 or k_py>0 else "-"}</td>'
                carrier_html += f'<td><b>{k_ms_cy:.1f}%</b></td><td>{k_ms_py:.1f}%</td><td>{k_ms_diff_str}</td>'
                carrier_html += '</tr>'

            tot_m_cy = df_top['Val_num'].sum()
            tot_m_py = df_top['Val_PY_num'].sum()
            tot_m_yoy = ((tot_m_cy - tot_m_py) / tot_m_py * 100) if tot_m_py > 0 else 0

            tot_c_sub = df_top[df_top[al_col_6].astype(str) == selected_carrier]
            tot_c_cy = tot_c_sub['Val_num'].sum()
            tot_c_py = tot_c_sub['Val_PY_num'].sum()
            tot_c_yoy = ((tot_c_cy - tot_c_py) / tot_c_py * 100) if tot_c_py > 0 else 0
            tot_c_ms_cy = (tot_c_cy / tot_m_cy * 100) if tot_m_cy > 0 else 0
            tot_c_ms_py = (tot_c_py / tot_m_py * 100) if tot_m_py > 0 else 0
            tot_c_ms_diff = tot_c_ms_cy - tot_c_ms_py

            tot_k_sub = df_top[df_top[al_col_6].astype(str) == 'KE']
            tot_k_cy = tot_k_sub['Val_num'].sum()
            tot_k_py = tot_k_sub['Val_PY_num'].sum()
            tot_k_yoy = ((tot_k_cy - tot_k_py) / tot_k_py * 100) if tot_k_py > 0 else 0
            tot_k_ms_cy = (tot_k_cy / tot_m_cy * 100) if tot_m_cy > 0 else 0
            tot_k_ms_py = (tot_k_py / tot_m_py * 100) if tot_m_py > 0 else 0
            tot_k_ms_diff = tot_k_ms_cy - tot_k_ms_py

            carrier_html += '<tr class="row-summary">'
            carrier_html += '<td colspan="2" style="text-align:center;">26년 요약</td>'
            carrier_html += f'<td>{tot_m_cy:,.0f}</td><td>{tot_m_py:,.0f}</td><td>{"▲" if tot_m_yoy>=0 else "▼"} {abs(tot_m_yoy):.0f}%</td>'
            carrier_html += f'<td>{tot_c_cy:,.0f}</td><td>{tot_c_py:,.0f}</td><td>{"▲" if tot_c_yoy>=0 else "▼"} {abs(tot_c_yoy):.0f}%</td>'
            carrier_html += f'<td>{tot_c_ms_cy:.0f}%</td><td>{tot_c_ms_py:.0f}%</td><td>{"▲" if tot_c_ms_diff>=0 else "▼"} {abs(tot_c_ms_diff):.0f}%p</td>'
            carrier_html += f'<td>{tot_k_cy:,.0f}</td><td>{tot_k_py:,.0f}</td><td>{"▲" if tot_k_yoy>=0 else "▼"} {abs(tot_k_yoy):.0f}%</td>'
            carrier_html += f'<td>{tot_k_ms_cy:.1f}%</td><td>{tot_k_ms_py:.1f}%</td><td>{"▲" if tot_k_ms_diff>=0 else "▼"} {abs(tot_k_ms_diff):.1f}%p</td>'
            carrier_html += '</tr>'

            carrier_html += '</tbody></table></div>'
            st.markdown(carrier_html, unsafe_allow_html=True)

    with tab6_3:
        st.markdown("*(속도 최적화를 위해 상위 1,000건만 조율 표출합니다)*")
        st.dataframe(filtered_6.head(1000), width="stretch")