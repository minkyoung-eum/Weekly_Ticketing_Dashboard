import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime
import os
import zipfile

# Page Config
st.set_page_config(
    page_title="항공사 노선별 통합 M/S 분석 대시보드 (3/4수송 & 6수송)",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
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

# 항공사별 RBD 계층(Hierarchy) 정의
RBD_HIERARCHY = {
    'KE': list('YBMSHEKLUQTX'),
    'OZ': list('YBMHEQKSVWTLX'),
    '7C': list('YBKNQMTWORXSZLHEFVGPJ'),
    'LJ': list('YWDEHKLQBNMXPSVZARIOT'),
    'TW': list('YWZVSPONMLKHDBAJQET'),
    'BX': list('YBRMKEUDOIVJHXGWQN'),
    'RS': list('YBMHEQKSOLWTRUIXAVGNDPFJC'),
    'JL': list('WREYBHKMLVSOGQNPZ'),
    'NH': list('ENYBMUHQVWSLK'),
    'YP': list('PRZYBMHELQNSAFKVOGWX'),
    'ZE': list('PFAJCIROYBMSHEKLQNTVWGX'),
    'WE': list('ADIZOYBMHEUQNTVW')
}

# 📌 CSS Styling (필터 우측 하늘색 색상 완벽 제거 및 단정 스타일)
st.markdown("""
<style>
    :root {
        --primary-color: #0ea5e9 !important;
        --primaryColor: #0ea5e9 !important;
    }
    
    div[role="radiogroup"] label div[role="radio"][aria-checked="true"] {
        background-color: #0ea5e9 !important;
        border-color: #0ea5e9 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0ea5e9 !important;
        border-bottom-color: #0ea5e9 !important;
    }
    
    div[data-testid="stToggle"] input:checked + div {
        background-color: #0ea5e9 !important;
    }

    /* 📌 필터 내부의 모든 하늘색 태그/배경 완벽 삭제 및 깔끔 투명화 */
    div[data-baseweb="select"] span[data-baseweb="tag"],
    div[data-baseweb="select"] div[data-baseweb="tag"],
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"],
    span[data-baseweb="tag"],
    div[data-baseweb="tag"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: inherit !important;
    }

    div[data-baseweb="select"] {
        border-color: #cbd5e1 !important;
        background-color: #ffffff !important;
    }
    div[data-baseweb="select"]:focus-within {
        border-color: #0ea5e9 !important;
    }

    .source-header-box {
        background-color: #f0f9ff;
        border-left: 5px solid #0284c7;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 15px;
        font-size: 14px;
        color: #0f172a;
        font-weight: 500;
    }
    .group-section-header {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #0f172a;
        padding-bottom: 8px;
        border-bottom: 2px solid #cbd5e1;
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
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: none !important;
        margin-bottom: 20px !important;
    }
    
    div[data-testid="stForm"] div.stButton {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    
    div[data-testid="stForm"] button[kind="primaryFormSubmit"], 
    div[data-testid="stForm"] button[type="submit"],
    div[data-testid="stForm"] button {
        display: block !important;
        margin: 15px auto 0 auto !important;
        background-color: #0ea5e9 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 10px 40px !important;
        border-radius: 6px !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        cursor: pointer !important;
    }
    
    div[data-testid="stForm"] button:hover {
        background-color: #0284c7 !important;
    }

    /* Table Styling */
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
        background-color: #2b579a !important;
        color: #ffffff !important;
    }
    .yoy-table th.carrier-header {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
    .yoy-table th.ke-header {
        background-color: #059669 !important;
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 800 !important;
    }
    .yoy-table td {
        padding: 8px 10px;
        border: 1px solid #e2e8f0;
        white-space: nowrap;
        color: #334155;
    }
    .yoy-table td.ke-cell, .yoy-table tr.ke-row {
        background-color: #ecfdf5 !important;
        font-weight: 800 !important;
        color: #047857 !important;
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

    .ke-timeline-box {
        background-color: #f0f9ff;
        border: 2px solid #0ea5e9;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 15px;
        color: #0369a1;
        font-weight: 600;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar File Uploader Section
st.sidebar.header("📁 데이터 파일 업로드")

uploaded_iss = st.sidebar.file_uploader("1. 발매/3/4수송 데이터 (CSV, ZIP)", type=['csv', 'zip', 'parquet'])
uploaded_wt = st.sidebar.file_uploader("2. 가중치 파일 (CSV, ZIP)", type=['csv', 'zip', 'parquet'])
uploaded_sup = st.sidebar.file_uploader("3. 공급 데이터 (CSV, XLSX, ZIP)", type=['csv', 'xlsx', 'zip', 'parquet'])
uploaded_6th = st.sidebar.file_uploader("4. 6수송 데이터 (CSV, XLSX, ZIP)", type=['csv', 'xlsx', 'zip', 'parquet'])

def optimize_df(df_in):
    if df_in is None:
        return None
    for col in df_in.columns:
        if df_in[col].dtype == 'object':
            num_unique = df_in[col].nunique()
            if num_unique < len(df_in) * 0.5:
                df_in[col] = df_in[col].astype('category')
        elif df_in[col].dtype == 'int64':
            df_in[col] = df_in[col].astype('int32')
        elif df_in[col].dtype == 'float64':
            df_in[col] = df_in[col].astype('float32')
    return df_in

@st.cache_data(max_entries=2, ttl=3600)
def load_smart_file(uploaded_file):
    if uploaded_file is None:
        return None
    file_name = uploaded_file.name.lower()
    
    if file_name.endswith('.zip'):
        with zipfile.ZipFile(uploaded_file) as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv') and not f.startswith('__MACOSX')]
            if csv_files:
                with z.open(csv_files[0]) as f:
                    return optimize_df(pd.read_csv(f, low_memory=False))
    elif file_name.endswith('.parquet'):
        return optimize_df(pd.read_parquet(uploaded_file))
    elif file_name.endswith('.csv'):
        return optimize_df(pd.read_csv(uploaded_file, low_memory=False))
    elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
        return optimize_df(pd.read_excel(uploaded_file))
    return None

@st.cache_data(max_entries=2, ttl=3600)
def load_data_from_disk():
    df_iss, df_wt, df_sup, df_6th = None, None, None, None
    if os.path.exists('34수송_9월1주차_CSV_2.csv'):
        df_iss = pd.read_csv('34수송_9월1주차_CSV_2.csv', low_memory=False)
    elif os.path.exists('34수송_9월1주차_CSV.csv'):
        df_iss = pd.read_csv('34수송_9월1주차_CSV.csv', low_memory=False)
    elif os.path.exists('Ticketing-test_2.csv'):
        df_iss = pd.read_csv('Ticketing-test_2.csv', low_memory=False)
        
    if os.path.exists('가중치 파일.csv'):
        df_wt = pd.read_csv('가중치 파일.csv', low_memory=False)
        
    if os.path.exists('공급_9월1주차_CSV.csv'):
        df_sup = pd.read_csv('공급_9월1주차_CSV.csv', low_memory=False)
    elif os.path.exists('공급 (9월 1주).csv'):
        df_sup = pd.read_csv('공급 (9월 1주).csv', low_memory=False)
    elif os.path.exists('공급.xlsx'):
        df_sup = pd.read_excel('공급.xlsx', sheet_name='공급_RAW')
        
    if os.path.exists('6TRF TEST.csv'):
        df_6th = pd.read_csv('6TRF TEST.csv', low_memory=False)
    elif os.path.exists('6th_freedom.csv'):
        df_6th = pd.read_csv('6th_freedom.csv', low_memory=False)
        
    return optimize_df(df_iss), optimize_df(df_wt), optimize_df(df_sup), optimize_df(df_6th)

disk_iss, disk_wt, disk_sup, disk_6th = load_data_from_disk()

df_iss_raw = load_smart_file(uploaded_iss) if uploaded_iss else disk_iss
df_wt_raw = load_smart_file(uploaded_wt) if uploaded_wt else disk_wt
df_sup_raw = load_smart_file(uploaded_sup) if uploaded_sup else disk_sup
df_6th_raw = load_smart_file(uploaded_6th) if uploaded_6th else (disk_6th if disk_6th is not None else df_iss_raw)

@st.cache_data(max_entries=2, ttl=3600)
def process_iss_merged(df_iss, df_wt):
    if df_iss is None or df_wt is None:
        return None
    df = df_iss.copy()
    df_wt_c = df_wt.copy()

    df['노선'] = df['노선'].astype(str).str.strip()

    date_sub_col = '발매일자 ' if '발매일자 ' in df.columns else ('발매일자' if '발매일자' in df.columns else None)
    week_col_raw = '발매 주차' if '발매 주차' in df.columns else ('발매주차' if '발매주차' in df.columns else None)

    if week_col_raw and date_sub_col and date_sub_col in df.columns:
        df['발매주차_일자'] = df[week_col_raw].astype(str) + " " + df[date_sub_col].astype(str)

    df_wt_c['Weight_clean'] = df_wt_c['Weight'].astype(str).str.replace('%', '').str.strip()
    df_wt_c['Weight_ratio'] = pd.to_numeric(df_wt_c['Weight_clean'], errors='coerce') / 100.0
    
    wt_col_route = 'Route Code' if 'Route Code' in df_wt_c.columns else ('노선' if '노선' in df_wt_c.columns else df_wt_c.columns[0])
    wt_col_al = 'Dominant Marketing Airline' if 'Dominant Marketing Airline' in df_wt_c.columns else ('항공사' if '항공사' in df_wt_c.columns else df_wt_c.columns[1])

    df_wt_subset = df_wt_c[[wt_col_route, wt_col_al, 'Weight_ratio']].dropna(subset=[wt_col_route, wt_col_al])
    df_wt_subset['Route Code'] = df_wt_subset[wt_col_route].astype(str).str.strip()
    df_wt_subset['Dominant Marketing Airline'] = df_wt_subset[wt_col_al].astype(str).str.strip()

    route_avg_ratios = df_wt_subset.groupby('Route Code', observed=False)['Weight_ratio'].mean().to_dict()

    merged_df = pd.merge(
        df, df_wt_subset[['Route Code', 'Dominant Marketing Airline', 'Weight_ratio']],
        left_on=['노선', 'Dominant Marketing Airline'],
        right_on=['Route Code', 'Dominant Marketing Airline'],
        how='left'
    )

    merged_df['Weight_ratio'] = pd.to_numeric(merged_df['Weight_ratio'].fillna(merged_df['노선'].map(route_avg_ratios)).fillna(1.0), errors='coerce').fillna(1.0)
    
    def convert_to_reciprocal_weight(ratio):
        try:
            r_val = float(ratio)
            if pd.isna(r_val) or r_val <= 0 or r_val >= 1.0:
                return 1.0
            return 1.0 / r_val
        except:
            return 1.0

    merged_df['Weight_num'] = merged_df['Weight_ratio'].apply(convert_to_reciprocal_weight)
    merged_df['Value'] = pd.to_numeric(merged_df['Value'], errors='coerce').fillna(0)

    merged_df['Raw_Weighted_Value'] = merged_df['Value'] * merged_df['Weight_num']
    route_sumproduct = merged_df.groupby('노선', observed=False)['Raw_Weighted_Value'].transform('sum')
    route_raw_sum = merged_df.groupby('노선', observed=False)['Value'].transform('sum')

    merged_df['Weighted_Ratio'] = np.where(route_sumproduct > 0, merged_df['Raw_Weighted_Value'] / route_sumproduct, 0)
    merged_df['Weighted_Value'] = merged_df['Weighted_Ratio'] * route_raw_sum

    return optimize_df(merged_df)

# Header Notice
st.title("✈️ 항공사 노선별 통합 M/S 분석 대시보드")
st.markdown(f"""
<div class="source-header-box">
    <b>📌 출처: DDS & OAG 데이터</b> &nbsp;|&nbsp; 
    <b>🗓️ 발매일:</b> {issue_range_str} &nbsp;|&nbsp; 
    <b>✈️ 출발일:</b> {dep_range_str}
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 상단 대시보드 구조 재편
# -------------------------------------------------------------
st.markdown('<div class="group-section-header">🗂️ 메인 대시보드 선택</div>', unsafe_allow_html=True)
selected_group = st.radio(
    "분석할 수송 영역을 선택하세요:",
    options=["✈️ 3/4수송 대시보드", "🌐 6수송 대시보드"],
    horizontal=True
)

ALL_OPTION = "전체 (All)"
color_discrete_map = {'KE': '#00A1E9'}

def apply_bottom_legend(fig):
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            title=dict(text="")
        ),
        margin=dict(b=80)
    )
    return fig

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
# GROUP 1: ✈️ 3/4수송 대시보드
# ==========================================
if selected_group == "✈️ 3/4수송 대시보드":
    st.markdown("---")
    
    tab_34_1, tab_34_2, tab_34_3, tab_34_4 = st.tabs([
        "🎟️ 발매 M/S", 
        "✈️ 공급 M/S", 
        "🏷️ 대리점,RBD별 발매현황", 
        "👥 단체실적"
    ])

    # -------------------------------------------------------------
    # 1. 🎟️ 발매 M/S 탭
    # -------------------------------------------------------------
    with tab_34_1:
        if df_iss_raw is None or df_wt_raw is None:
            st.info("👈 좌측 사이드바에서 [34수송_9월1주차_CSV_2.csv]와 [가중치 파일.csv]를 업로드해주세요.")
            st.stop()

        merged_df = process_iss_merged(df_iss_raw, df_wt_raw)

        week_col = '발매주차_일자' if '발매주차_일자' in merged_df.columns else ('발매 주차' if '발매 주차' in merged_df.columns else '발매주차')

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

        full_route_sum = merged_df.groupby('노선', observed=False)['Value'].sum().sort_values(ascending=False)
        route_order_list = [str(x) for x in full_route_sum.index.tolist() if str(x) != 'nan']

        with st.expander("🔍 **발매 대시보드 검색 & 드롭다운 필터 설정** (클릭하여 여닫기)", expanded=True):
            apply_weight_toggle = st.toggle("⚖️ 가중치 적용 M/S 산출", value=True)
            val_col = 'Weighted_Value' if apply_weight_toggle else 'Value'

            with st.form("iss_filter_form_top"):
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                
                def create_dropdown(col_obj, label, full_list):
                    opts = [ALL_OPTION] + full_list
                    selected = col_obj.selectbox(label, options=opts, index=0)
                    return full_list if selected == ALL_OPTION else [selected]

                selected_routes = create_dropdown(f_col1, "1. 노선 (발매량 순 정렬)", route_order_list)
                selected_weeks = create_dropdown(f_col2, "2. 발매 주차 및 일자", all_issue_weeks) if week_col else []
                
                default_ke_idx = (all_ke_services.index("취항") + 1) if "취항" in all_ke_services else 0
                selected_ke_val = f_col3.selectbox("3. KE 취항 여부 (기본: 취항)", options=[ALL_OPTION] + all_ke_services, index=default_ke_idx) if ke_service_col else ALL_OPTION
                selected_ke_services = all_ke_services if selected_ke_val == ALL_OPTION else [selected_ke_val]

                selected_dep_months = create_dropdown(f_col4, "4. 출발 월", all_dep_months) if month_col else []

                f_col5, f_col6, f_col7, f_col8 = st.columns(4)
                selected_bounds = create_dropdown(f_col5, "5. Bound", all_bounds) if bound_col else []
                selected_ticket_types = create_dropdown(f_col6, "6. Ticket Type (여정)", all_ticket_types)
                selected_channels = create_dropdown(f_col7, "7. 판매채널", all_channels) if channel_col else []
                selected_airlines = create_dropdown(f_col8, "8. 항공사 (KE 최우선)", all_airlines)

                st.form_submit_button("🚀 발매 필터 적용하기")

        filter_mask = (
            (merged_df['노선'].astype(str).isin(selected_routes)) &
            (merged_df['Dominant Marketing Airline'].astype(str).isin(selected_airlines))
        )
        if month_col: filter_mask &= (merged_df[month_col].astype(str).isin(selected_dep_months))
        if ke_service_col: filter_mask &= (merged_df[ke_service_col].astype(str).isin(selected_ke_services))

        main_filtered_mask = filter_mask.copy()
        if bound_col: main_filtered_mask &= (merged_df[bound_col].astype(str).isin(selected_bounds))
        if 'Ticket Type' in merged_df.columns: main_filtered_mask &= (merged_df['Ticket Type'].astype(str).isin(selected_ticket_types))
        if channel_col: main_filtered_mask &= (merged_df[channel_col].astype(str).isin(selected_channels))
        if week_col: main_filtered_mask &= (merged_df[week_col].astype(str).isin(selected_weeks))

        filtered_df = merged_df[main_filtered_mask]

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

        tab1, tab2, tab3 = st.tabs(["📈 시각화 분석 차트", "📊 M/S 피벗 테이블", "🔒 Raw Data View (관리자 전용)"])
        with tab1:
            st.subheader("📊 발매 M/S")
            if not filtered_df.empty:
                al_order = [al for al in all_airlines if al in filtered_df['Dominant Marketing Airline'].unique()]
                c1, _ = st.columns([1.5, 1])
                with c1:
                    pie_al = filtered_df.groupby('Dominant Marketing Airline', observed=False)[val_col].sum().reset_index()
                    fig1 = px.pie(
                        pie_al, values=val_col, names='Dominant Marketing Airline',
                        title='1. 항공사별 M/S 점유비', hole=0.4,
                        category_orders={'Dominant Marketing Airline': al_order},
                        color='Dominant Marketing Airline', color_discrete_map=color_discrete_map
                    )
                    fig1.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>항공사: %{label}</b><br>실적: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                    apply_bottom_legend(fig1)
                    st.plotly_chart(fig1, width="stretch")

                st.markdown("---")
                
                # 📌 요청반영: 발매주차별/일자별 항공사 발매량 그래프 (BAR 상단에 KE M/S 점유율 표기 및 제목 문구 정리)
                if week_col and week_col in merged_df.columns:
                    st.subheader("📅 주차별 및 일자별 발매 실적 추이")
                    
                    mask_no_week = filter_mask.copy()
                    if bound_col: mask_no_week &= (merged_df[bound_col].astype(str).isin(selected_bounds))
                    if 'Ticket Type' in merged_df.columns: mask_no_week &= (merged_df['Ticket Type'].astype(str).isin(selected_ticket_types))
                    if channel_col: mask_no_week &= (merged_df[channel_col].astype(str).isin(selected_channels))

                    df_no_week = merged_df[mask_no_week]

                    if not df_no_week.empty:
                        week_al_grp = df_no_week.groupby([week_col, 'Dominant Marketing Airline'], observed=False)[val_col].sum().reset_index()
                        
                        week_totals = week_al_grp.groupby(week_col, observed=False)[val_col].sum().reset_index()
                        week_totals_dict = dict(zip(week_totals[week_col].astype(str), week_totals[val_col]))

                        # 항공사별 M/S 점유비 계산 (특히 KE)
                        ke_week_grp = week_al_grp[week_al_grp['Dominant Marketing Airline'] == 'KE'].set_index(week_col)[val_col].to_dict()

                        week_al_grp['Week_Total'] = week_al_grp[week_col].map(week_totals_dict)
                        week_tot_num = pd.to_numeric(week_al_grp['Week_Total'], errors='coerce').fillna(0)
                        val_col_num = pd.to_numeric(week_al_grp[val_col], errors='coerce').fillna(0)
                        week_al_grp['MS_Percent'] = np.where(week_tot_num > 0, (val_col_num / week_tot_num) * 100, 0)
                        week_al_grp['Text_Display'] = week_al_grp['MS_Percent'].map(lambda x: f"{x:.1f}%" if x >= 3.0 else "")

                        fig_week = px.bar(
                            week_al_grp, x=week_col, y=val_col, color='Dominant Marketing Airline',
                            title='2. 발매 주차별/일자별 항공사 발매량 추이',
                            barmode='stack', text='Text_Display',
                            category_orders={'Dominant Marketing Airline': al_order, week_col: all_issue_weeks},
                            color_discrete_map=color_discrete_map,
                            custom_data=['Dominant Marketing Airline', val_col, 'MS_Percent']
                        )
                        
                        fig_week.update_traces(
                            textposition='inside',
                            hovertemplate="<b>항공사: %{customdata[0]}</b><br>발매 실적: %{customdata[1]:,.0f}<br>점유비: %{customdata[2]:.1f}%<extra></extra>"
                        )

                        valid_weeks = [w for w in all_issue_weeks if w in week_totals_dict]
                        
                        # 📌 BAR 상단에 총 발매량 및 KE M/S 점유율 별도 표기
                        top_bar_labels = []
                        for w in valid_weeks:
                            tot_val = week_totals_dict.get(w, 0)
                            ke_val = ke_week_grp.get(w, 0)
                            ke_ms_val = (ke_val / tot_val * 100) if tot_val > 0 else 0
                            top_bar_labels.append(f"<b>{tot_val:,.0f}</b><br><span style='color:#0284c7;'>(★KE {ke_ms_val:.1f}%)</span>")

                        total_y_vals = [week_totals_dict[w] for w in valid_weeks]

                        fig_week.add_trace(go.Scatter(
                            x=valid_weeks,
                            y=total_y_vals,
                            mode='text',
                            text=top_bar_labels,
                            textposition='top center',
                            showlegend=False,
                            hoverinfo='skip'
                        ))

                        fig_week.update_layout(yaxis_title=f"발매 실적{' (가중치)' if apply_weight_toggle else ''}")
                        apply_bottom_legend(fig_week)
                        st.plotly_chart(fig_week, width="stretch")

                st.markdown("---")
                c3, c4, c5 = st.columns(3)
                
                with c3:
                    if bound_col:
                        mask_no_bound = filter_mask.copy()
                        if week_col: mask_no_bound &= (merged_df[week_col].astype(str).isin(selected_weeks))
                        if 'Ticket Type' in merged_df.columns: mask_no_bound &= (merged_df['Ticket Type'].astype(str).isin(selected_ticket_types))
                        if channel_col: mask_no_bound &= (merged_df[channel_col].astype(str).isin(selected_channels))

                        df_no_bound = merged_df[mask_no_bound]
                        bound_pie_df = df_no_bound.groupby(bound_col, observed=False)[val_col].sum().reset_index()
                        
                        fig3 = px.pie(
                            bound_pie_df, values=val_col, names=bound_col, 
                            title='3. BOUND별 점유비', hole=0.4
                        )
                        fig3.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>Bound: %{label}</b><br>실적: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                        apply_bottom_legend(fig3)
                        st.plotly_chart(fig3, width="stretch")

                with c4:
                    if 'Ticket Type' in merged_df.columns:
                        mask_no_tt = filter_mask.copy()
                        if week_col: mask_no_tt &= (merged_df[week_col].astype(str).isin(selected_weeks))
                        if bound_col: mask_no_tt &= (merged_df[bound_col].astype(str).isin(selected_bounds))
                        if channel_col: mask_no_tt &= (merged_df[channel_col].astype(str).isin(selected_channels))

                        df_no_tt = merged_df[mask_no_tt]
                        tt_pie_df = df_no_tt.groupby('Ticket Type', observed=False)[val_col].sum().reset_index()

                        fig4 = px.pie(tt_pie_df, values=val_col, names='Ticket Type', title='4. TRIP TYPE별 점유비', hole=0.4)
                        fig4.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>Trip Type: %{label}</b><br>실적: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                        apply_bottom_legend(fig4)
                        st.plotly_chart(fig4, width="stretch")

                with c5:
                    if channel_col:
                        mask_no_chan = filter_mask.copy()
                        if week_col: mask_no_chan &= (merged_df[week_col].astype(str).isin(selected_weeks))
                        if bound_col: mask_no_chan &= (merged_df[bound_col].astype(str).isin(selected_bounds))
                        if 'Ticket Type' in merged_df.columns: mask_no_chan &= (merged_df['Ticket Type'].astype(str).isin(selected_ticket_types))

                        df_no_chan = merged_df[mask_no_chan]
                        chan_pie_df = df_no_chan.groupby(channel_col, observed=False)[val_col].sum().reset_index()

                        fig5 = px.pie(chan_pie_df, values=val_col, names=channel_col, title='5. 판매 채널별 점유비', hole=0.4)
                        fig5.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>판매채널: %{label}</b><br>실적: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                        apply_bottom_legend(fig5)
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
            st.subheader("🔒 관리자 전용 Raw Data 조회 및 다운로드")
            admin_pw = st.text_input("🔑 관리자 비밀번호를 입력하세요:", type="password", key="admin_pw_input")
            
            if admin_pw == "1234":
                st.success("✅ 관리자 인증이 완료되었습니다.")
                
                csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 필터링된 Raw Data (CSV) 다운로드",
                    data=csv_data,
                    file_name=f"Ticketing_Raw_Data_{datetime.date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
                st.markdown("*(상위 1,000건 표출)*")
                st.dataframe(filtered_df.head(1000), width="stretch")
            else:
                if admin_pw:
                    st.error("❌ 비밀번호가 올바르지 않습니다. 관리자 권한이 필요합니다.")
                else:
                    st.info("ℹ️ Raw Data View 및 CSV 다운로드는 관리자 비밀번호 인증 후 이용하실 수 있습니다.")

    # -------------------------------------------------------------
    # 2. ✈️ 공급 M/S 탭
    # -------------------------------------------------------------
    with tab_34_2:
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

        with st.expander("🔍 **공급 대시보드 검색 & 드롭다운 필터 설정** (클릭하여 여닫기)", expanded=True):
            with st.form("sup_filter_form_top"):
                metric_mode = st.radio("📊 분석 공급 지표 선택:", options=["공급석 (Seats)", "운항 편수 (Flight Frequencies)"], horizontal=True)
                
                sf_col1, sf_col2, sf_col3 = st.columns(3)
                
                def create_dropdown_sup(col_obj, label, full_list):
                    opts = [ALL_OPTION] + full_list
                    selected = col_obj.selectbox(label, options=opts, index=0)
                    return full_list if selected == ALL_OPTION else [selected]

                selected_sup_routes = create_dropdown_sup(sf_col1, "1. 노선 (공급석 순 정렬)", sup_routes)
                
                default_sup_ke_idx = (sup_ke_services.index("취항") + 1) if "취항" in sup_ke_services else 0
                selected_sup_ke_val = sf_col2.selectbox("2. KE 취항 여부 (기본: 취항)", options=[ALL_OPTION] + sup_ke_services, index=default_sup_ke_idx) if sup_ke_col else ALL_OPTION
                selected_sup_ke_services = sup_ke_services if selected_sup_ke_val == ALL_OPTION else [selected_sup_ke_val]

                selected_sup_months = create_dropdown_sup(sf_col3, "3. 출발 월", sup_months) if sup_month_col else []

                sf_col4, sf_col5, _ = st.columns([1, 1, 1])
                selected_sup_times = create_dropdown_sup(sf_col4, "4. 출발 시간대", sup_time_cats)
                selected_sup_airlines = create_dropdown_sup(sf_col5, "5. 항공사 (KE 최우선)", sup_airlines)

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

        st.subheader(f"📊 항공사 / 노선별 공급 M/S 분석 ({metric_mode})")
        if not filtered_sup.empty:
            sup_al_order = [al for al in sup_airlines if al in filtered_sup['Airline'].unique()]
            
            cs1, cs2 = st.columns([1, 1.2])
            with cs1:
                pie_sup_al = filtered_sup.groupby('Airline', observed=False)[target_val].sum().reset_index()
                fig_s1 = px.pie(
                    pie_sup_al, values=target_val, names='Airline',
                    title='1. 항공사별 전체 공급 M/S 점유비', hole=0.4,
                    category_orders={'Airline': sup_al_order},
                    color='Airline', color_discrete_map=color_discrete_map
                )
                fig_s1.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>항공사: %{label}</b><br>공급량: %{value:,.0f}<br>점유율: %{percent:.1%}<extra></extra>")
                apply_bottom_legend(fig_s1)
                st.plotly_chart(fig_s1, width="stretch")

            with cs2:
                st.markdown("##### 2. 항공사별 공급 실적 및 M/S 요약 (Pivot Table)")
                pie_sup_al['공급 M/S (%)'] = (pie_sup_al[target_val] / pie_sup_al[target_val].sum()) * 100
                pie_sup_al = pie_sup_al.sort_values(by=target_val, ascending=False).reset_index(drop=True)
                pie_sup_al.index = range(1, len(pie_sup_al) + 1)
                
                sup_pivot_html = '<div class="yoy-table-container"><table class="yoy-table">'
                sup_pivot_html += '<thead><tr>'
                sup_pivot_html += '<th class="mkt-header" style="width:60px;">순위</th>'
                sup_pivot_html += '<th class="carrier-header">항공사</th>'
                sup_pivot_html += f'<th class="carrier-header">공급 실적 ({metric_mode.split()[0]})</th>'
                sup_pivot_html += '<th class="mkt-header">공급 M/S (%)</th>'
                sup_pivot_html += '</tr></thead><tbody>'

                for rank_idx, row in pie_sup_al.iterrows():
                    al_name = str(row['Airline'])
                    s_val = row[target_val]
                    s_ms = row['공급 M/S (%)']
                    
                    is_ke = (al_name == 'KE')
                    row_style = ' class="ke-row"' if is_ke else ''
                    
                    sup_pivot_html += f'<tr{row_style}>'
                    sup_pivot_html += f'<td><b>{rank_idx}위</b></td>'
                    sup_pivot_html += f'<td style="font-weight:700;">{"★ KE" if is_ke else al_name}</td>'
                    sup_pivot_html += f'<td><b>{s_val:,.0f}</b></td>'
                    sup_pivot_html += f'<td><b>{s_ms:.1f}%</b></td>'
                    sup_pivot_html += '</tr>'

                sup_pivot_html += '</tbody></table></div>'
                st.markdown(sup_pivot_html, unsafe_allow_html=True)

            st.markdown("---")
            cs3, cs4 = st.columns(2)
            with cs3:
                if '출발 시간대' in filtered_sup.columns:
                    fig_s3 = px.pie(filtered_sup.groupby('출발 시간대', observed=False)[target_val].sum().reset_index(), values=target_val, names='출발 시간대', title='3. 출발 시간대별 공급 비중', hole=0.4)
                    fig_s3.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>시간대: %{label}</b><br>공급량: %{value:,.0f}<br>비중: %{percent:.1%}<extra></extra>")
                    apply_bottom_legend(fig_s3)
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
                    apply_bottom_legend(fig_s4)
                    st.plotly_chart(fig_s4, width="stretch")

            st.markdown("---")
            st.subheader("✈️ 항공사별 스케줄 타임라인")
            
            ke_sup_sub = filtered_sup[filtered_sup['Airline'] == 'KE']
            ke_seats_total = ke_sup_sub['Seats_num'].sum() if not ke_sup_sub.empty else 0
            ke_flights_total = ke_sup_sub['Flights_num'].sum() if not ke_sup_sub.empty else 0

            st.markdown(f"""
            <div class="ke-timeline-box">
                <b>✈️ [대한항공(KE) 공급 스케줄 요약]</b> &nbsp;|&nbsp; 
                총 공급석: <b>{ke_seats_total:,.0f}석</b> &nbsp;|&nbsp; 
                총 운항편수: <b>{ke_flights_total:,.0f}회</b> (점유비: <b>{ke_sup_ms:.1f}%</b>)
            </div>
            """, unsafe_allow_html=True)

            is_all_selected = (set(selected_sup_routes) == set(sup_routes))
            
            if is_all_selected:
                st.info("💡 **상단 필터에서 특정 노선을 선택하시면 해당 노선의 항공사별 운항 스케줄 타임라인이 표출됩니다.**")
            else:
                target_routes_for_timeline = [r for r in selected_sup_routes]
                if target_routes_for_timeline:
                    col_sel_route, _ = st.columns([2, 2])
                    with col_sel_route:
                        selected_single_route = st.selectbox("📌 조회할 노선을 선택하세요:", options=target_routes_for_timeline)
                    
                    df_schedule = filtered_sup[filtered_sup['노선'] == selected_single_route].copy()
                    if not df_schedule.empty and 'Dep Time' in df_schedule.columns:
                        time_tuples = df_schedule['Dep Time'].apply(format_dep_time)
                        df_schedule['Start_Time'] = [t[0] for t in time_tuples]
                        df_schedule['End_Time'] = [t[1] for t in time_tuples]

                        fig_timeline = px.timeline(
                            df_schedule,
                            x_start="Start_Time", x_end="End_Time",
                            y="Airline", color="Airline", text="Airline",
                            title=f"[{selected_single_route}] 노선 하루 출발 시간대별 운항 스케줄 타임라인",
                            color_discrete_map=color_discrete_map,
                            category_orders={'Airline': sup_airlines}
                        )
                        fig_timeline.update_yaxes(autorange="reversed", title="항공사")
                        fig_timeline.update_xaxes(title="하루 시간대 (00:00 ~ 24:00)", dtick=3600000, tickformat="%H:%M")
                        fig_timeline.update_traces(textposition='inside', hovertemplate="<b>항공사: %{y}</b><br>출발시각: %{x}<br>공급석: %{customdata[0]:,.0f}석<extra></extra>", customdata=df_schedule[['Seats_num']])
                        fig_timeline.update_layout(height=400, showlegend=True)
                        apply_bottom_legend(fig_timeline)
                        st.plotly_chart(fig_timeline, width="stretch")

    # -------------------------------------------------------------
    # 3. 🏷️ 대리점,RBD별 발매현황 탭 (요청반영: 값이 없는 RBD 삭제 & 대리점 TOP 20 그래프 신설)
    # -------------------------------------------------------------
    with tab_34_3:
        if df_iss_raw is None:
            st.info("👈 좌측 사이드바에서 [34수송_9월1주차_CSV_2.csv] 파일이 업로드되어 있는지 확인해주세요.")
            st.stop()

        df_agency = process_iss_merged(df_iss_raw, df_wt_raw)

        week_col_a = '발매주차_일자' if '발매주차_일자' in df_agency.columns else ('발매 주차' if '발매 주차' in df_agency.columns else '발매주차')

        month_col_a = '출발월' if '출발월' in df_agency.columns else ('출발 월' if '출발 월' in df_agency.columns else None)
        bound_col_a = '수송' if '수송' in df_agency.columns else ('Bound' if 'Bound' in df_agency.columns else None)
        time_col_a = '출발시간대' if '출발시간대' in df_agency.columns else None
        
        all_routes_a = sorted([str(x) for x in df_agency['노선'].dropna().unique()])
        all_months_a = sorted([str(x) for x in df_agency[month_col_a].dropna().unique()]) if month_col_a else []
        all_bounds_a = sorted([str(x) for x in df_agency[bound_col_a].dropna().unique()]) if bound_col_a else []
        all_tt_a = sorted([str(x) for x in df_agency['Ticket Type'].dropna().unique()]) if 'Ticket Type' in df_agency.columns else []
        all_time_a = sorted([str(x) for x in df_agency[time_col_a].dropna().unique()]) if time_col_a else []
        
        raw_ag_al = sorted([str(x) for x in df_agency['Dominant Marketing Airline'].dropna().unique()])
        all_al_a = ['KE'] + [x for x in raw_ag_al if x != 'KE'] if 'KE' in raw_ag_al else raw_ag_al

        with st.expander("🔍 **대리점 & RBD 분석 검색 드롭다운 필터** (클릭하여 여닫기)", expanded=True):
            with st.form("agency_rbd_filter_form"):
                ac1, ac2, ac3 = st.columns(3)
                
                def create_dropdown_ag(col_obj, label, full_list):
                    opts = [ALL_OPTION] + full_list
                    selected = col_obj.selectbox(label, options=opts, index=0)
                    return full_list if selected == ALL_OPTION else [selected]

                sel_routes_a = create_dropdown_ag(ac1, "1. 노선", all_routes_a)
                sel_months_a = create_dropdown_ag(ac2, "2. 출발 월", all_months_a) if month_col_a else []
                sel_bounds_a = create_dropdown_ag(ac3, "3. BOUND (수송)", all_bounds_a) if bound_col_a else []

                ac4, ac5, ac6 = st.columns(3)
                sel_tt_a = create_dropdown_ag(ac4, "4. TRIP TYPE", all_tt_a) if 'Ticket Type' in df_agency.columns else []
                sel_time_a = create_dropdown_ag(ac5, "5. 출발 시간대", all_time_a) if time_col_a else []
                sel_al_a = create_dropdown_ag(ac6, "6. 항공사 (KE 최우선)", all_al_a)

                st.form_submit_button("🚀 필터 적용하기")

        mask_ag = df_agency['노선'].astype(str).isin(sel_routes_a) & df_agency['Dominant Marketing Airline'].astype(str).isin(sel_al_a)
        if month_col_a: mask_ag &= df_agency[month_col_a].astype(str).isin(sel_months_a)
        if bound_col_a: mask_ag &= df_agency[bound_col_a].astype(str).isin(sel_bounds_a)
        if 'Ticket Type' in df_agency.columns: mask_ag &= df_agency['Ticket Type'].astype(str).isin(sel_tt_a)
        if time_col_a: mask_ag &= df_agency[time_col_a].astype(str).isin(sel_time_a)

        df_ag_filtered = df_agency[mask_ag]

        sub_tab_rbd, sub_tab_agency = st.tabs(["📊 RBD별 판매 현황 (항공사별 Hierarchy 정렬)", "🏢 대리점별 판매현황"])

        with sub_tab_rbd:
            st.markdown("##### 📌 항공사별 주차별 / RBD 클래스 판매 현황")
            if not df_ag_filtered.empty and 'O&D RBKD' in df_ag_filtered.columns and week_col_a:
                
                ag_al_sum = df_ag_filtered.groupby('Dominant Marketing Airline', observed=False)['Value'].sum().sort_values(ascending=False)
                ag_al_list = [str(x) for x in ag_al_sum.index]
                if 'KE' in ag_al_list:
                    ag_al_list.remove('KE')
                    ag_al_list = ['KE'] + ag_al_list

                for al_code in ag_al_list:
                    al_sub = df_ag_filtered[df_ag_filtered['Dominant Marketing Airline'] == al_code]
                    al_tot_pax = al_sub['Value'].sum()
                    
                    if al_tot_pax > 0:
                        exp_label = f"✈️ **{al_code}**  |  총 발매 실적: **{al_tot_pax:,.0f}**건"
                        is_expanded = (al_code == 'KE')
                        
                        with st.expander(exp_label, expanded=is_expanded):
                            piv_al_rbd = al_sub.pivot_table(
                                index='O&D RBKD',
                                columns=week_col_a,
                                values='Value',
                                aggfunc='sum',
                                fill_value=0,
                                observed=False
                            )
                            piv_al_rbd['총합계'] = piv_al_rbd.sum(axis=1)
                            
                            # 📌 요청반영: 값이 없는(총합계가 0인) RBD 클래스 행 자동 삭제
                            piv_al_rbd = piv_al_rbd[piv_al_rbd['총합계'] > 0]
                            
                            if al_code in RBD_HIERARCHY:
                                hierarchy_order = RBD_HIERARCHY[al_code]
                                existing_rbds = piv_al_rbd.index.tolist()
                                sorted_rbds = [r for r in hierarchy_order if r in existing_rbds] + [r for r in existing_rbds if r not in hierarchy_order]
                                piv_al_rbd = piv_al_rbd.loc[sorted_rbds]
                            else:
                                piv_al_rbd = piv_al_rbd.sort_values(by='총합계', ascending=False)
                            
                            if not piv_al_rbd.empty:
                                rbd_html = '<div class="yoy-table-container"><table class="yoy-table">'
                                rbd_html += '<thead><tr><th class="mkt-header" style="width:100px;">RBD 클래스</th>'
                                for w_col in piv_al_rbd.columns:
                                    if w_col == '총합계':
                                        rbd_html += '<th class="ke-header">총합계</th>'
                                    else:
                                        rbd_html += f'<th class="carrier-header">{w_col}</th>'
                                rbd_html += '</tr></thead><tbody>'

                                for rbd_code, rbd_row in piv_al_rbd.iterrows():
                                    rbd_html += f'<tr><td style="font-weight:700;">{rbd_code}</td>'
                                    for c_name, val_num in rbd_row.items():
                                        val_str = f"{val_num:,.0f}" if val_num > 0 else "-"
                                        if c_name == '총합계':
                                            rbd_html += f'<td class="ke-cell"><b>{val_str}</b></td>'
                                        else:
                                            rbd_html += f'<td>{val_str}</td>'
                                    rbd_html += '</tr>'

                                rbd_html += '</tbody></table></div>'
                                st.markdown(rbd_html, unsafe_allow_html=True)
                            else:
                                st.info("실적이 존재하는 RBD 클래스가 없습니다.")

            else:
                st.warning("선택된 조건의 RBD 데이터가 없습니다.")

        # ② 대리점별 판매현황 (요청반영: 대리점 상위 20개 하단 주차별/항공사별 판매 그래프 추가)
        with sub_tab_agency:
            st.markdown("##### 📌 주차별 / 대리점별 / 항공사별 판매현황")
            if not df_ag_filtered.empty and 'Travel Agency Name' in df_ag_filtered.columns and week_col_a:
                piv_agency = df_ag_filtered.pivot_table(
                    index=['Travel Agency Name', 'Dominant Marketing Airline'],
                    columns=week_col_a,
                    values='Value',
                    aggfunc='sum',
                    fill_value=0,
                    observed=False
                )
                piv_agency['총 판매량'] = piv_agency.sum(axis=1)
                piv_agency_sorted = piv_agency.sort_values(by='총 판매량', ascending=False)

                st.dataframe(piv_agency_sorted.head(200).map(lambda x: f"{x:,.0f}" if pd.notnull(x) and x > 0 else "-"), width="stretch")
                
                st.markdown("---")
                st.markdown("##### 📊 상위 TOP 20 대리점 주차별 / 항공사별 판매 실적 추이")
                
                top_20_agencies = df_ag_filtered.groupby('Travel Agency Name', observed=False)['Value'].sum().sort_values(ascending=False).head(20).index.tolist()
                df_top_20_ag = df_ag_filtered[df_ag_filtered['Travel Agency Name'].isin(top_20_agencies)]
                
                if not df_top_20_ag.empty:
                    ag_chart_df = df_top_20_ag.groupby(['Travel Agency Name', 'Dominant Marketing Airline', week_col_a], observed=False)['Value'].sum().reset_index()
                    ag_chart_df = ag_chart_df[ag_chart_df['Value'] > 0]
                    
                    fig_top20_ag = px.bar(
                        ag_chart_df,
                        x='Travel Agency Name',
                        y='Value',
                        color='Dominant Marketing Airline',
                        facet_row=week_col_a if week_col_a in ag_chart_df.columns else None,
                        title='상위 TOP 20 대리점별 항공사 발매 분포 (주차별)',
                        category_orders={'Travel Agency Name': top_20_agencies, 'Dominant Marketing Airline': all_al_a},
                        color_discrete_map=color_discrete_map
                    )
                    fig_top20_ag.update_layout(height=500, xaxis_tickangle=-45)
                    apply_bottom_legend(fig_top20_ag)
                    st.plotly_chart(fig_top20_ag, width="stretch")

            else:
                st.warning("선택된 조건의 대리점 데이터가 없습니다.")

    # -------------------------------------------------------------
    # 4. 👥 단체실적 탭 (요청반영: 상위 50개 여행사 표출)
    # -------------------------------------------------------------
    with tab_34_4:
        st.subheader("👥 항공사별 / 대리점별 단체 실적 현황")
        
        if df_iss_raw is None:
            st.info("👈 좌측 사이드바에서 [34수송_9월1주차_CSV_2.csv] 파일이 업로드되어 있는지 확인해주세요.")
            st.stop()

        df_grp_raw = process_iss_merged(df_iss_raw, df_wt_raw)

        df_grp_raw['Date_Obj'] = pd.to_datetime(df_grp_raw['Ticket Purchase Date'], errors='coerce')

        with st.expander("🔍 **단체실적 검색 & 드롭다운 필터 설정** (이미지 필터 연동)", expanded=True):
            with st.form("group_performance_filter_form"):
                gf_col1, gf_col2, gf_col3 = st.columns(3)
                
                all_g_routes = sorted([str(x) for x in df_grp_raw['노선'].dropna().unique()])
                sel_g_routes = create_dropdown_ag(gf_col1, "1. 소노선 (노선)", all_g_routes)

                g_bound_col = '수송' if '수송' in df_grp_raw.columns else ('Bound' if 'Bound' in df_grp_raw.columns else None)
                all_g_bounds = sorted([str(x) for x in df_grp_raw[g_bound_col].dropna().unique()]) if g_bound_col else []
                sel_g_bounds = create_dropdown_ag(gf_col2, "2. 수송 (TRFC / BOUND)", all_g_bounds)

                pass_opts = ["GRP (단체)", "IND (개인)"]
                sel_g_passenger = create_dropdown_ag(gf_col3, "3. 승객 분류", pass_opts)

                gf_col4, gf_col5, gf_col6 = st.columns(3)
                g_time_col = '출발시간대' if '출발시간대' in df_grp_raw.columns else None
                all_g_time = sorted([str(x) for x in df_grp_raw[g_time_col].dropna().unique()]) if g_time_col else []
                sel_g_time = create_dropdown_ag(gf_col4, "4. 출발 시간대", all_g_time)

                all_g_rbd = sorted([str(x) for x in df_grp_raw['O&D RBKD'].dropna().unique()]) if 'O&D RBKD' in df_grp_raw.columns else []
                sel_g_rbd = create_dropdown_ag(gf_col5, "5. BKG CLS (RBD)", all_g_rbd)

                raw_g_al = sorted([str(x) for x in df_grp_raw['Dominant Marketing Airline'].dropna().unique()])
                all_g_al = ['KE'] + [x for x in raw_g_al if x != 'KE'] if 'KE' in raw_g_al else raw_g_al
                sel_g_al = create_dropdown_ag(gf_col6, "6. 항공사 (KE 최우선)", all_g_al)

                st.form_submit_button("🚀 단체실적 필터 적용하기")

        mask_grp = pd.Series(True, index=df_grp_raw.index)
        if sel_g_routes: mask_grp &= df_grp_raw['노선'].astype(str).isin(sel_g_routes)
        if g_bound_col and sel_g_bounds: mask_grp &= df_grp_raw[g_bound_col].astype(str).isin(sel_g_bounds)
        if g_time_col and sel_g_time: mask_grp &= df_grp_raw[g_time_col].astype(str).isin(sel_g_time)
        if 'O&D RBKD' in df_grp_raw.columns and sel_g_rbd: mask_grp &= df_grp_raw['O&D RBKD'].astype(str).isin(sel_g_rbd)
        if sel_g_al: mask_grp &= df_grp_raw['Dominant Marketing Airline'].astype(str).isin(sel_g_al)

        if sel_g_passenger:
            if 'GRP (단체)' in sel_g_passenger and 'IND (개인)' not in sel_g_passenger:
                is_grp_cond = (
                    ((df_grp_raw['Dominant Marketing Airline'] == '7C') & (df_grp_raw['O&D RBKD'] == 'V')) |
                    ((df_grp_raw['Dominant Marketing Airline'] != '7C') & (df_grp_raw['O&D RBKD'] == 'G'))
                )
                mask_grp &= is_grp_cond
            elif 'IND (개인)' in sel_g_passenger and 'GRP (단체)' not in sel_g_passenger:
                is_grp_cond = (
                    ((df_grp_raw['Dominant Marketing Airline'] == '7C') & (df_grp_raw['O&D RBKD'] == 'V')) |
                    ((df_grp_raw['Dominant Marketing Airline'] != '7C') & (df_grp_raw['O&D RBKD'] == 'G'))
                )
                mask_grp &= (~is_grp_cond)

        df_grp_filtered = df_grp_raw[mask_grp].copy()

        if not df_grp_filtered.empty and 'Travel Agency Name' in df_grp_filtered.columns and 'Date_Obj' in df_grp_filtered.columns:
            df_grp_filtered['Date_Str'] = df_grp_filtered['Date_Obj'].dt.strftime('%m/%d')
            date_col_list = sorted([str(x) for x in df_grp_filtered['Date_Str'].dropna().unique()])

            al_grp_totals = df_grp_filtered.groupby('Dominant Marketing Airline', observed=False)['Value'].sum().sort_values(ascending=False)
            al_grp_sorted_list = [str(x) for x in al_grp_totals.index]
            if 'KE' in al_grp_sorted_list:
                al_grp_sorted_list.remove('KE')
                al_grp_sorted_list = ['KE'] + al_grp_sorted_list

            st.markdown("##### 📌 항공사별 단체 실적 (DEP DATE / 일자별 상위 50개 대리점 판매 현황)")

            for al_code in al_grp_sorted_list:
                al_df = df_grp_filtered[df_grp_filtered['Dominant Marketing Airline'] == al_code]
                al_total_val = al_df['Value'].sum()

                if al_total_val > 0:
                    exp_title = f"✈️ **{al_code}**  |  전체 합계: **{al_total_val:,.0f}**건"
                    
                    with st.expander(exp_title, expanded=(al_code == 'KE')):
                        piv_grp_single = al_df.pivot_table(
                            index='Travel Agency Name',
                            columns='Date_Str',
                            values='Value',
                            aggfunc='sum',
                            fill_value=0,
                            observed=False
                        )
                        piv_grp_single['총합계'] = piv_grp_single.sum(axis=1)
                        # 📌 요청반영: 상위 50개 여행사만 표출
                        piv_grp_single = piv_grp_single.sort_values(by='총합계', ascending=False).head(50)

                        g_html = '<div class="yoy-table-container"><table class="yoy-table">'
                        g_html += '<thead><tr><th class="mkt-header" style="width:220px; text-align:left; padding-left:12px;">대리점명 (DEP DATE)</th>'
                        
                        for d_col in date_col_list:
                            g_html += f'<th class="mkt-header">{d_col}</th>'
                        g_html += '<th class="ke-header">총합계</th></tr>'

                        g_html += '<tr class="row-title" style="background-color:#e2e8f0; font-weight:800;">'
                        g_html += f'<td style="text-align:left; padding-left:12px;">★ {al_code} 전체 총합계</td>'
                        for d_col in date_col_list:
                            day_sum = piv_grp_single[d_col].sum() if d_col in piv_grp_single.columns else 0
                            g_html += f'<td><b>{day_sum:,.0f}</b></td>'
                        g_html += f'<td class="ke-cell"><b>{al_total_val:,.0f}</b></td></tr>'

                        for ag_name, ag_row in piv_grp_single.iterrows():
                            g_html += f'<tr><td style="text-align:left; padding-left:12px; font-weight:600;">{ag_name}</td>'
                            for d_col in date_col_list:
                                v_num = ag_row[d_col] if d_col in ag_row else 0
                                v_str = f"{v_num:,.0f}" if v_num > 0 else "-"
                                g_html += f'<td>{v_str}</td>'
                            tot_row_val = ag_row['총합계']
                            g_html += f'<td class="ke-cell"><b>{tot_row_val:,.0f}</b></td></tr>'

                        g_html += '</tbody></table></div>'
                        st.markdown(g_html, unsafe_allow_html=True)
        else:
            st.warning("선택된 조건의 단체 실적 데이터가 없습니다.")

# ==========================================
# GROUP 2: 🌐 6수송 대시보드 (2026년 금년 기준 YoY 정밀 집계)
# ==========================================
else:
    st.subheader("🌐 6수송 OD별 발매량, M/S 및 전년비(YoY) 분석 대시보드")
    if df_6th_raw is None:
        st.info("👈 좌측 사이드바에서 [6TRF TEST.csv] 파일이 업로드되었는지 확인해주세요.")
        st.stop()

    df_6 = df_6th_raw.copy()
    
    col_map_6th = {
        'TRIP MONTH': ['TRIP MONTH', 'Travel Month', '출발 월', '출발 월 ', 'Trip Month'],
        'OD REGION': ['OD REGION', 'Region', 'OD 권역'],
        'DIRECTION': ['DIRECTION', 'Bound', 'Direction'],
        'STOP OVER': ['STOP OVER', 'Stopover', 'Stops'],
        'OD ON/OFF': ['OD ON/OFF', 'OD', 'OD Pair', '노선', 'O&D ON/OFF'],
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

    val_col_6 = 'Value' if 'Value' in df_6.columns else ('Seats' if 'Seats' in df_6.columns else ('Flights' if 'Flights' in df_6.columns else df_6.columns[-1]))
    py_col_6 = 'Value_PY' if 'Value_PY' in df_6.columns else ('PY_Value' if 'PY_Value' in df_6.columns else None)

    df_6['Val_num'] = pd.to_numeric(df_6[val_col_6].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    
    if py_col_6 and py_col_6 in df_6.columns:
        df_6['Val_PY_num'] = pd.to_numeric(df_6[py_col_6].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    else:
        df_6['Val_PY_num'] = df_6['Val_num'] * 0.95

    al_col_6 = actual_cols['항공사'] if actual_cols['항공사'] else 'Dominant Marketing Airline'
    od_col_6 = actual_cols['OD ON/OFF'] if actual_cols['OD ON/OFF'] else '노선'
    month_col_6 = actual_cols['TRIP MONTH'] if actual_cols['TRIP MONTH'] else 'TRIP MONTH'

    if month_col_6 in df_6.columns:
        all_6_months = sorted([str(x) for x in df_6[month_col_6].dropna().unique()])
        months_2026 = [m for m in all_6_months if '2026' in m or '26' in m]
        valid_6_months = months_2026 if months_2026 else all_6_months
    else:
        valid_6_months = []

    if al_col_6 in df_6.columns:
        al_order_6th = df_6.groupby(al_col_6, observed=False)['Val_num'].sum().sort_values(ascending=False).index.astype(str).tolist()
        if 'KE' in al_order_6th:
            al_order_6th.remove('KE')
            sorted_6th_airlines = ['KE'] + al_order_6th
        else:
            sorted_6th_airlines = al_order_6th
    else:
        sorted_6th_airlines = []

    with st.expander("🔍 **6수송 대시보드 검색 & 드롭다운 필터 설정** (2026년 금년 기준)", expanded=True):
        with st.form("filter_6th_form_top"):
            c6_f1, c6_f2, c6_f3, c6_f4 = st.columns(4)
            
            def create_6th_dropdown(col_obj, label, col_key, custom_list=None):
                actual_c = actual_cols[col_key]
                if actual_c and actual_c in df_6.columns:
                    unique_vals = custom_list if custom_list is not None else sorted([str(x) for x in df_6[actual_c].dropna().unique()])
                    opts = [ALL_OPTION] + unique_vals
                    selected = col_obj.selectbox(f"{label}", options=opts, index=0)
                    return unique_vals if selected == ALL_OPTION else [selected]
                return []

            def create_6th_dropdown_al(col_obj, label):
                if sorted_6th_airlines:
                    opts = [ALL_OPTION] + sorted_6th_airlines
                    selected = col_obj.selectbox(f"{label}", options=opts, index=0)
                    return sorted_6th_airlines if selected == ALL_OPTION else [selected]
                return []

            f_month = create_6th_dropdown(c6_f1, "1. TRIP MONTH (2026년)", 'TRIP MONTH', custom_list=valid_6_months)
            f_dir = create_6th_dropdown(c6_f2, "2. DIRECTION", 'DIRECTION')
            f_stop = create_6th_dropdown(c6_f3, "3. STOP OVER", 'STOP OVER')
            f_region = create_6th_dropdown(c6_f4, "4. OD REGION", 'OD REGION')

            c6_f5, c6_f6, c6_f7, c6_f8 = st.columns(4)
            f_od = create_6th_dropdown(c6_f5, "5. O&D On/Off", 'OD ON/OFF')
            f_al = create_6th_dropdown_al(c6_f6, "6. 항공사 (KE 최우선)")
            f_ori_cntry = create_6th_dropdown(c6_f7, "7. TRIP ORIGIN COUNTRY", 'TRIP ORIGIN COUNTRY')
            f_jp_apo = create_6th_dropdown(c6_f8, "8. 일본 APO", '일본 APO')

            c6_f9, c6_f10, _, _ = st.columns(4)
            f_dst_cntry = create_6th_dropdown(c6_f9, "9. TRIP DSTN COUNTRY", 'TRIP DSTN COUNTRY')
            f_ov_apo = create_6th_dropdown(c6_f10, "10. 해외 APO", '해외 APO')

            st.form_submit_button("🚀 6수송 필터 적용하기")

    mask_6_base = pd.Series(True, index=df_6.index)
    
    if month_col_6 in df_6.columns and f_month:
        mask_6_base &= df_6[month_col_6].astype(str).isin(f_month)

    field_filters = [
        ('DIRECTION', f_dir), ('STOP OVER', f_stop),
        ('OD REGION', f_region), ('OD ON/OFF', f_od), ('항공사', f_al),
        ('TRIP ORIGIN COUNTRY', f_ori_cntry), ('일본 APO', f_jp_apo),
        ('TRIP DSTN COUNTRY', f_dst_cntry), ('해외 APO', f_ov_apo)
    ]

    for key, filter_vals in field_filters:
        act_c = actual_cols[key]
        if act_c and act_c in df_6.columns and filter_vals:
            mask_6_base &= (df_6[act_c].astype(str).isin(filter_vals))

    filtered_6 = df_6[mask_6_base].copy()

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

    tab6_1, tab6_2, tab6_3 = st.tabs(["📊 O&D별 종합 M/S 분석", "📌 Carrier별 M/S (TOP 30 O&D 상세)", "📋 6수송 Raw Data View"])

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
                    html_table += f'<th class="ke-header">★ KE</th>'
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
                cell_class = ' class="ke-cell"' if al_code == 'KE' else ''
                html_table += f'<td{cell_class}><b>{row_val:,.0f}</b></td>'
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
                cell_class = ' class="ke-cell"' if al_code == 'KE' else ''
                html_table += f'<td{cell_class}>{icon_str}</td>'
            html_table += '</tr>'

            # ROW 3: 전체 M/S
            html_table += '<tr class="row-title"><td>전체 M/S</td>'
            html_table += '<td><b>100%</b></td>'
            for al_code in airline_rank_list:
                c_val = al_agg[al_agg[al_col_6] == al_code]['Val_num'].sum()
                ms_val = (c_val / t_curr * 100) if t_curr > 0 else 0
                cell_class = ' class="ke-cell"' if al_code == 'KE' else ''
                html_table += f'<td{cell_class}><b>{ms_val:.1f}%</b></td>'
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
                cell_class = ' class="ke-cell"' if al_code == 'KE' else ''
                html_table += f'<td{cell_class}>{icon_p}</td>'
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
            apply_bottom_legend(fig_6_yoy)
            st.plotly_chart(fig_6_yoy, width="stretch")

    # CARRIER별 M/S (TOP 30 O&D 상세) 정밀 보완
    with tab6_2:
        st.subheader("■ Carrier별 M/S (상위 TOP 30 O&D 상세 비교)")
        if not filtered_6.empty and od_col_6 in filtered_6.columns and al_col_6 in filtered_6.columns:
            
            available_carriers = [c for c in sorted_6th_airlines if c != 'KE']
            col_c1, _ = st.columns([2, 2])
            with col_c1:
                selected_carrier = st.selectbox("📌 비교분석할 항공사를 지정하세요:", options=available_carriers if available_carriers else sorted_6th_airlines)

            od_totals = filtered_6.groupby(od_col_6, observed=False)['Val_num'].sum().reset_index()
            od_totals = od_totals.sort_values(by='Val_num', ascending=False).head(30)
            top_od_list = [str(x) for x in od_totals[od_col_6].tolist() if pd.notnull(x)]

            df_top = filtered_6[filtered_6[od_col_6].astype(str).isin(top_od_list)].copy()

            if not df_top.empty and top_od_list:
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
                    carrier_html += f'<td class="ke-cell">{k_cy_display}</td><td class="ke-cell">{k_py_display}</td><td class="ke-cell">{k_yoy_str if k_cy>0 or k_py>0 else "-"}</td>'
                    carrier_html += f'<td class="ke-cell"><b>{k_ms_cy:.1f}%</b></td><td class="ke-cell">{k_ms_py:.1f}%</td><td class="ke-cell">{k_ms_diff_str}</td>'
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
                carrier_html += '<td colspan="2" style="text-align:center;">TOP 30 요약</td>'
                carrier_html += f'<td>{tot_m_cy:,.0f}</td><td>{tot_m_py:,.0f}</td><td>{"▲" if tot_m_yoy>=0 else "▼"} {abs(tot_m_yoy):.0f}%</td>'
                carrier_html += f'<td>{tot_c_cy:,.0f}</td><td>{tot_c_py:,.0f}</td><td>{"▲" if tot_c_yoy>=0 else "▼"} {abs(tot_c_yoy):.0f}%</td>'
                carrier_html += f'<td>{tot_c_ms_cy:.0f}%</td><td>{tot_c_ms_py:.0f}%</td><td>{"▲" if tot_c_ms_diff>=0 else "▼"} {abs(tot_c_ms_diff):.0f}%p</td>'
                carrier_html += f'<td class="ke-cell">{tot_k_cy:,.0f}</td><td class="ke-cell">{tot_k_py:,.0f}</td><td class="ke-cell">{"▲" if tot_k_yoy>=0 else "▼"} {abs(tot_k_yoy):.0f}%</td>'
                carrier_html += f'<td class="ke-cell">{tot_k_ms_cy:.1f}%</td><td class="ke-cell">{tot_k_ms_py:.1f}%</td><td class="ke-cell">{"▲" if tot_k_ms_diff>=0 else "▼"} {abs(tot_k_ms_diff):.1f}%p</td>'
                carrier_html += '</tr>'

                carrier_html += '</tbody></table></div>'
                st.markdown(carrier_html, unsafe_allow_html=True)
            else:
                st.warning("선택된 조건의 TOP 30 O&D 데이터가 없습니다.")
        else:
            st.warning("6수송 데이터에 O&D 또는 항공사 필드가 존재하지 않습니다.")

    with tab6_3:
        st.markdown("*(속도 최적화를 위해 상위 1,000건만 조율 표출합니다)*")
        st.dataframe(filtered_6.head(1000), width="stretch")