import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page Config
st.set_page_config(
    page_title="항공사 / 노선별 M/S 대시보드",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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

@st.cache_data
def load_data():
    ticketing_path = 'Ticketing-test_2.csv'
    weight_path = '가중치 파일.csv'
    
    df_ticketing = None
    df_weight = None
    
    if os.path.exists(ticketing_path):
        df_ticketing = pd.read_csv(ticketing_path, low_memory=False)
        cols_to_drop = [c for c in df_ticketing.columns if 'Unnamed' in c]
        if cols_to_drop:
            df_ticketing = df_ticketing.drop(columns=cols_to_drop)
            
    if os.path.exists(weight_path):
        df_weight = pd.read_csv(weight_path)
        
    return df_ticketing, df_weight

df_raw, df_wt_raw = load_data()

st.title("✈️ 항공사 / 노선별 M/S 대시보드")
st.caption("Ticketing-test_2.csv & 가중치 파일.csv 기반 실시간 가중 M/S 분석 시스템")

if df_raw is None or df_wt_raw is None:
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        u_file1 = st.file_uploader("Ticketing-test_2.csv 업로드", type=['csv'])
        if u_file1:
            df_raw = pd.read_csv(u_file1, low_memory=False)
    with col_u2:
        u_file2 = st.file_uploader("가중치 파일.csv 업로드", type=['csv'])
        if u_file2:
            df_wt_raw = pd.read_csv(u_file2)
            
    if df_raw is None or df_wt_raw is None:
        st.info("두 가중치/티케팅 CSV 파일이 모두 필요합니다. 파일 위치를 확인해주세요.")
        st.stop()

# Data Preprocessing & Merging Weight
df = df_raw.copy()
df_wt = df_wt_raw.copy()

# Parse Weight %
df_wt['Weight_clean'] = df_wt['Weight'].astype(str).str.replace('%', '').str.strip()
df_wt['Weight_num'] = pd.to_numeric(df_wt['Weight_clean'], errors='coerce') / 100.0

df_wt_subset = df_wt[['Route Code', 'Dominant Marketing Airline', 'Weight_num']].dropna(subset=['Route Code', 'Dominant Marketing Airline'])

# Merge Weight
merged_df = pd.merge(
    df,
    df_wt_subset,
    left_on=['노선', 'Dominant Marketing Airline'],
    right_on=['Route Code', 'Dominant Marketing Airline'],
    how='left'
)

# Fill Missing Weights with 1.0 (100%)
merged_df['Weight_num'] = merged_df['Weight_num'].fillna(1.0)
merged_df['Value'] = pd.to_numeric(merged_df['Value'], errors='coerce').fillna(0)
merged_df['Weighted_Value'] = merged_df['Value'] * merged_df['Weight_num']

# Sidebar Filters
st.sidebar.header("🔍 대시보드 필터 (Slicers)")

apply_weight_toggle = st.sidebar.toggle("⚖️ 가중치 적용 M/S 산출", value=True)
val_col = 'Weighted_Value' if apply_weight_toggle else 'Value'

ALL_OPTION = "전체 (All)"

def get_filter_selection(label, full_list, default_to_all=True):
    options = [ALL_OPTION] + full_list
    default = [ALL_OPTION] if default_to_all else options
    selected = st.sidebar.multiselect(label, options=options, default=default)
    
    if ALL_OPTION in selected or not selected:
        return full_list
    return selected

# 노선 발매량 순 정렬 목록
route_order_list = merged_df.groupby('노선')[val_col].sum().sort_values(ascending=False).index.tolist()
all_dep_months = sorted([str(x) for x in merged_df['출발 월'].dropna().unique()])
all_bounds = sorted([str(x) for x in merged_df['Bound'].dropna().unique()])
all_ticket_types = sorted([str(x) for x in merged_df['Ticket Type'].dropna().unique()])
all_channels = sorted([str(x) for x in merged_df['판매채널'].dropna().unique()])
all_airlines = sorted([str(x) for x in merged_df['Dominant Marketing Airline'].dropna().unique()])

# 1. 노선
selected_routes = get_filter_selection("노선 (발매량 순)", route_order_list)
# 2. 출발 월
selected_dep_months = get_filter_selection("출발 월", all_dep_months)
# 3. Bound
selected_bounds = get_filter_selection("Bound", all_bounds)
# 4. Ticket Type (여정)
selected_ticket_types = get_filter_selection("Ticket Type (여정)", all_ticket_types)
# 5. 판매채널
selected_channels = get_filter_selection("판매채널", all_channels)
# 6. 항공사
selected_airlines = get_filter_selection("항공사", all_airlines)

# Filter Dataset
filtered_df = merged_df[
    (merged_df['노선'].astype(str).isin(selected_routes)) &
    (merged_df['출발 월'].astype(str).isin(selected_dep_months)) &
    (merged_df['Bound'].astype(str).isin(selected_bounds)) &
    (merged_df['Ticket Type'].astype(str).isin(selected_ticket_types)) &
    (merged_df['판매채널'].astype(str).isin(selected_channels)) &
    (merged_df['Dominant Marketing Airline'].astype(str).isin(selected_airlines))
]

# KPI Top Summary
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

total_pax = filtered_df[val_col].sum()

top_al = "-"
top_ms = 0.0
if not filtered_df.empty and total_pax > 0:
    al_sum = filtered_df.groupby('Dominant Marketing Airline')[val_col].sum()
    top_al = al_sum.idxmax()
    top_ms = (al_sum.max() / total_pax) * 100

top_route = "-"
if not filtered_df.empty:
    route_sum = filtered_df.groupby('노선')[val_col].sum()
    if not route_sum.empty:
        top_route = route_sum.idxmax()

status_wt_label = " (가중치 적용)" if apply_weight_toggle else " (순수 Raw)"

with col_m1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">총 발매 실적{status_wt_label}</div><div class="metric-value">{total_pax:,.0f}</div></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">1위 항공사 (M/S)</div><div class="metric-value" style="color:#1d4ed8;">{top_al} ({top_ms:.1f}%)</div></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">최대 실적 노선</div><div class="metric-value" style="color:#047857;">{top_route}</div></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">가중치 매칭 건수</div><div class="metric-value">{(filtered_df["Weight_num"] != 1.0).sum():,.0f}건</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Content
tab1, tab2, tab3 = st.tabs(["📈 시각화 분석 차트", "📊 M/S 피벗 테이블", "📋 Raw Data & Weight Match View"])

with tab1:
    st.subheader(f"📊 M/S 분석 시각화 대시보드{status_wt_label}")
    
    if not filtered_df.empty:
        # Row 1: 1. 항공사별 M/S 점유비 & 2. 주차별 항공사 실적 추이
        col_r1_1, col_r1_2 = st.columns(2)
        
        with col_r1_1:
            pie_al = filtered_df.groupby('Dominant Marketing Airline')[val_col].sum().reset_index()
            fig_pie_al = px.pie(
                pie_al, 
                values=val_col, 
                names='Dominant Marketing Airline', 
                title='1. 항공사별 M/S 점유비', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie_al.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>항공사: %{label}</b><br>실적: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>"
            )
            st.plotly_chart(fig_pie_al, use_container_width=True)
            
        with col_r1_2:
            df_chart_week = filtered_df.groupby(['발매주차', 'Dominant Marketing Airline'])[val_col].sum().reset_index()
            fig_week = px.bar(
                df_chart_week,
                x='발매주차',
                y=val_col,
                color='Dominant Marketing Airline',
                title='2. 주차별 항공사 실적 추이',
                barmode='stack',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_week.update_traces(
                hovertemplate="<b>주차: %{x}</b><br>항공사: %{fullData.name}<br>실적: %{y:,.0f}<extra></extra>"
            )
            fig_week.update_layout(xaxis_title="발매주차", yaxis_title="실적 (Pax)")
            st.plotly_chart(fig_week, use_container_width=True)

        st.markdown("---")
        
        # Row 2: 3. BOUND별 점유비 & 4. TRIP TYPE별 점유비 & 5. 판매 채널별 차트
        col_r2_1, col_r2_2, col_r2_3 = st.columns(3)
        
        with col_r2_1:
            pie_bound = filtered_df.groupby('Bound')[val_col].sum().reset_index()
            fig_bound = px.pie(
                pie_bound, 
                values=val_col, 
                names='Bound', 
                title='3. BOUND별 점유비', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_bound.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>Bound: %{label}</b><br>실적: %{value:,.0f}<br>비중: %{percent:.1%}<extra></extra>"
            )
            st.plotly_chart(fig_bound, use_container_width=True)

        with col_r2_2:
            pie_tt = filtered_df.groupby('Ticket Type')[val_col].sum().reset_index()
            fig_tt = px.pie(
                pie_tt, 
                values=val_col, 
                names='Ticket Type', 
                title='4. TRIP TYPE (여정)별 점유비', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_tt.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>Ticket Type: %{label}</b><br>실적: %{value:,.0f}<br>비중: %{percent:.1%}<extra></extra>"
            )
            st.plotly_chart(fig_tt, use_container_width=True)

        with col_r2_3:
            pie_channel = filtered_df.groupby('판매채널')[val_col].sum().reset_index()
            fig_channel = px.pie(
                pie_channel, 
                values=val_col, 
                names='판매채널', 
                title='5. 판매 채널별 점유비', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_channel.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>판매채널: %{label}</b><br>실적: %{value:,.0f}<br>비중: %{percent:.1%}<extra></extra>"
            )
            st.plotly_chart(fig_channel, use_container_width=True)

    else:
        st.info("선택된 필터 조건에 해당하는 데이터가 없습니다.")

with tab2:
    col_t1, col_t2 = st.columns([1.1, 1])
    
    with col_t1:
        st.markdown(f'<div class="section-header">📌 주차별 항공사 M/S 매트릭스{status_wt_label}</div>', unsafe_allow_html=True)
        if not filtered_df.empty:
            piv_week = filtered_df.pivot_table(
                index='Dominant Marketing Airline',
                columns='발매주차',
                values=val_col,
                aggfunc='sum',
                fill_value=0
            )
            
            week_order = ['7월 4주차', '7월 5주차', '8월 1주차', '8월 2주차', '8월 3주차', '8월 4주차']
            existing_weeks = [w for w in week_order if w in piv_week.columns] + [w for w in piv_week.columns if w not in week_order]
            piv_week = piv_week[existing_weeks]
            
            week_totals = piv_week.sum(axis=0)
            piv_week_ms = piv_week.divide(week_totals, axis=1) * 100
            
            total_by_al = filtered_df.groupby('Dominant Marketing Airline')[val_col].sum()
            piv_week_ms['총합계'] = (total_by_al / total_pax * 100) if total_pax > 0 else 0
            piv_week_ms = piv_week_ms.sort_values(by='총합계', ascending=False)
            
            formatted_week_ms = piv_week_ms.applymap(lambda x: f"{x:.1f}%" if pd.notnull(x) and x > 0 else "0.0%")
            st.dataframe(formatted_week_ms, use_container_width=True, height=450)
        else:
            st.info("선택된 필터 조건에 해당하는 데이터가 없습니다.")

    with col_t2:
        st.markdown(f'<div class="section-header">📌 노선별 항공사 M/S 매트릭스 (노선 발매량 순 정렬){status_wt_label}</div>', unsafe_allow_html=True)
        if not filtered_df.empty:
            piv_route = filtered_df.pivot_table(
                index='노선',
                columns='Dominant Marketing Airline',
                values=val_col,
                aggfunc='sum',
                fill_value=0
            )
            
            route_pax_sums = filtered_df.groupby('노선')[val_col].sum().sort_values(ascending=False)
            sorted_routes = [r for r in route_pax_sums.index if r in piv_route.index]
            piv_route = piv_route.loc[sorted_routes]
            
            route_totals = piv_route.sum(axis=1)
            piv_route_ms = piv_route.divide(route_totals, axis=0) * 100
            
            combined_rows = []
            for r in piv_route.index:
                val_row = piv_route.loc[r].apply(lambda x: f"{x:,.0f}")
                ms_row = piv_route_ms.loc[r].apply(lambda x: f"{x:.1f}%")
                
                val_row.name = (r, '실적')
                ms_row.name = (r, 'M/S')
                
                combined_rows.append(val_row)
                combined_rows.append(ms_row)
                
            df_route_display = pd.DataFrame(combined_rows)
            st.dataframe(df_route_display, use_container_width=True, height=450)
        else:
            st.info("선택된 필터 조건에 해당하는 데이터가 없습니다.")

with tab3:
    st.subheader("📋 Data Raw & Weight Match View")
    st.markdown("##### 가중치(Weight_num) 매칭 및 최종 Weighted_Value 적용 데이터")
    st.dataframe(filtered_df[['노선', 'Dominant Marketing Airline', '발매주차', '출발 월', 'Bound', 'Ticket Type', '판매채널', 'Value', 'Weight_num', 'Weighted_Value']], use_container_width=True)