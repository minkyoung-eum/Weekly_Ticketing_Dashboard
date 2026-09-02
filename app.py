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

# Styling
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
    file_path = 'Ticketing-test_2.csv'
    if os.path.exists(file_path):
        # Read low_memory=False for clean loading
        df = pd.read_csv(file_path, low_memory=False)
        # Drop empty columns
        cols_to_drop = [c for c in df.columns if 'Unnamed' in c]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        return df
    return None

df_raw = load_data()

st.title("✈️ 항공사 / 노선별 M/S 대시보드")
st.caption("Ticketing-test_2.csv 기반 실시간 M/S 분석 시스템")

if df_raw is None:
    uploaded_file = st.file_uploader("Ticketing-test_2.csv 파일을 업로드하세요", type=['csv'])
    if uploaded_file is not None:
        df_raw = pd.read_csv(uploaded_file, low_memory=False)
    else:
        st.info("CSV 파일을 폴더에 위치시키거나 위에서 업로드해주세요.")
        st.stop()

df = df_raw.copy()

# Ensure Value is numeric
df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)

# Sidebar Filters (Matching Slicers)
st.sidebar.header("🔍 대시보드 필터 (Slicers)")

# 1. 노선
all_routes = sorted([str(x) for x in df['노선'].dropna().unique()])
selected_routes = st.sidebar.multiselect("노선", options=all_routes, default=all_routes)

# 2. 출발 월
all_dep_months = sorted([str(x) for x in df['출발 월'].dropna().unique()])
selected_dep_months = st.sidebar.multiselect("출발 월", options=all_dep_months, default=all_dep_months)

# 3. Bound
all_bounds = sorted([str(x) for x in df['Bound'].dropna().unique()])
selected_bounds = st.sidebar.multiselect("Bound", options=all_bounds, default=all_bounds)

# 4. 여정 구별 (Ticket Type)
all_ticket_types = sorted([str(x) for x in df['Ticket Type'].dropna().unique()])
selected_ticket_types = st.sidebar.multiselect("Ticket Type (OW/RT)", options=all_ticket_types, default=all_ticket_types)

# 5. 판매채널
all_channels = sorted([str(x) for x in df['판매채널'].dropna().unique()])
selected_channels = st.sidebar.multiselect("판매채널", options=all_channels, default=all_channels)

# 6. 항공사 (Dominant Marketing Airline)
all_airlines = sorted([str(x) for x in df['Dominant Marketing Airline'].dropna().unique()])
top_defaults = [al for al in ['KE', 'OZ', '7C', 'LJ', 'TW', 'BX', 'RS', 'ZE'] if al in all_airlines]
selected_airlines = st.sidebar.multiselect("항공사", options=all_airlines, default=top_defaults if top_defaults else all_airlines)

# Filter Dataset
filtered_df = df[
    (df['노선'].astype(str).isin(selected_routes)) &
    (df['출발 월'].astype(str).isin(selected_dep_months)) &
    (df['Bound'].astype(str).isin(selected_bounds)) &
    (df['Ticket Type'].astype(str).isin(selected_ticket_types)) &
    (df['판매채널'].astype(str).isin(selected_channels)) &
    (df['Dominant Marketing Airline'].astype(str).isin(selected_airlines))
]

# KPI Top Summary
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

total_pax = filtered_df['Value'].sum()

top_al = "-"
top_ms = 0.0
if not filtered_df.empty and total_pax > 0:
    al_sum = filtered_df.groupby('Dominant Marketing Airline')['Value'].sum()
    top_al = al_sum.idxmax()
    top_ms = (al_sum.max() / total_pax) * 100

top_route = "-"
if not filtered_df.empty:
    route_sum = filtered_df.groupby('노선')['Value'].sum()
    if not route_sum.empty:
        top_route = route_sum.idxmax()

with col_m1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">총 실적 (Pax / Value)</div><div class="metric-value">{total_pax:,.0f}</div></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">1위 항공사 (M/S)</div><div class="metric-value" style="color:#1d4ed8;">{top_al} ({top_ms:.1f}%)</div></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">최대 운송 노선</div><div class="metric-value" style="color:#047857;">{top_route}</div></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">선택된 노선 수</div><div class="metric-value">{len(selected_routes)}개</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Dashboard Content
tab1, tab2, tab3 = st.tabs(["📊 M/S 피벗 테이블", "📈 시각화 분석 차트", "📋 Raw Data View"])

with tab1:
    col_t1, col_t2 = st.columns([1.1, 1])
    
    with col_t1:
        st.markdown('<div class="section-header">📌 주차별 항공사 M/S 매트릭스</div>', unsafe_allow_html=True)
        if not filtered_df.empty:
            piv_week = filtered_df.pivot_table(
                index='Dominant Marketing Airline',
                columns='발매주차',
                values='Value',
                aggfunc='sum',
                fill_value=0
            )
            
            # Sort columns in standard week order if present
            week_order = ['7월 4주차', '7월 5주차', '8월 1주차', '8월 2주차', '8월 3주차', '8월 4주차']
            existing_weeks = [w for w in week_order if w in piv_week.columns] + [w for w in piv_week.columns if w not in week_order]
            piv_week = piv_week[existing_weeks]
            
            # Calculate percentages
            week_totals = piv_week.sum(axis=0)
            piv_week_ms = piv_week.divide(week_totals, axis=1) * 100
            
            # Add Total M/S
            total_by_al = filtered_df.groupby('Dominant Marketing Airline')['Value'].sum()
            piv_week_ms['총합계'] = (total_by_al / total_pax * 100) if total_pax > 0 else 0
            piv_week_ms = piv_week_ms.sort_values(by='총합계', ascending=False)
            
            formatted_week_ms = piv_week_ms.applymap(lambda x: f"{x:.1f}%" if pd.notnull(x) and x > 0 else "0.0%")
            st.dataframe(formatted_week_ms, use_container_width=True, height=420)
        else:
            st.info("선택된 필터 조건에 해당하는 데이터가 없습니다.")

    with col_t2:
        st.markdown('<div class="section-header">📌 노선별 항공사 M/S 매트릭스</div>', unsafe_allow_html=True)
        if not filtered_df.empty:
            piv_route = filtered_df.pivot_table(
                index='노선',
                columns='Dominant Marketing Airline',
                values='Value',
                aggfunc='sum',
                fill_value=0
            )
            route_totals = piv_route.sum(axis=1)
            piv_route_ms = piv_route.divide(route_totals, axis=0) * 100
            
            # Combine Seats/Pax and M/S
            combined_rows = []
            for r in piv_route.index:
                val_row = piv_route.loc[r].apply(lambda x: f"{x:,.0f}")
                ms_row = piv_route_ms.loc[r].apply(lambda x: f"{x:.1f}%")
                
                val_row.name = (r, '실적')
                ms_row.name = (r, 'M/S')
                
                combined_rows.append(val_row)
                combined_rows.append(ms_row)
                
            df_route_display = pd.DataFrame(combined_rows)
            st.dataframe(df_route_display, use_container_width=True, height=420)
        else:
            st.info("선택된 필터 조건에 해당하는 데이터가 없습니다.")

with tab2:
    st.subheader("📈 시각화 분석")
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        if not filtered_df.empty:
            df_chart1 = filtered_df.groupby(['발매주차', 'Dominant Marketing Airline'])['Value'].sum().reset_index()
            fig1 = px.bar(
                df_chart1,
                x='발매주차',
                y='Value',
                color='Dominant Marketing Airline',
                title='주차별 항공사 실적 추이',
                barmode='stack'
            )
            st.plotly_chart(fig1, use_container_width=True)
            
    with col_c2:
        if not filtered_df.empty:
            df_chart2 = filtered_df.groupby(['노선', 'Dominant Marketing Airline'])['Value'].sum().reset_index()
            fig2 = px.bar(
                df_chart2,
                x='노선',
                y='Value',
                color='Dominant Marketing Airline',
                title='노선별 항공사 실적 비교',
                barmode='group'
            )
            st.plotly_chart(fig2, use_container_width=True)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if not filtered_df.empty:
            pie_al = filtered_df.groupby('Dominant Marketing Airline')['Value'].sum().reset_index()
            fig_pie1 = px.pie(pie_al, values='Value', names='Dominant Marketing Airline', title='전체 항공사 M/S 점유율', hole=0.35)
            st.plotly_chart(fig_pie1, use_container_width=True)
            
    with col_d2:
        if not filtered_df.empty:
            pie_channel = filtered_df.groupby('판매채널')['Value'].sum().reset_index()
            fig_pie2 = px.pie(pie_channel, values='Value', names='판매채널', title='판매채널별 비중', hole=0.35)
            st.plotly_chart(fig_pie2, use_container_width=True)

with tab3:
    st.subheader("📋 Raw Data View")
    st.dataframe(filtered_df, use_container_width=True)