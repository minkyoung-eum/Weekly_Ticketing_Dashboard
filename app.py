import io
import re
import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="주차별 발매 분석 대시보드", layout="wide"
)

# 세션 상태 초기화
if "raw_df" not in st.session_state:
    st.session_state["raw_df"] = None
if "weight_df" not in st.session_state:
    st.session_state["weight_df"] = None


# ---------------------------------------------------------
# 🚀 속도 개선 핵심: 메모리 가공 및 카테고리 형변환 최적화
# ---------------------------------------------------------
@st.cache_data(max_entries=2, show_spinner=False)
def load_uploaded_file(file_bytes, filename):
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))
    return df


def get_iso_month_week(date):
    if pd.isna(date):
        return ""
    try:
        dt = pd.to_datetime(date)
        iso_year, iso_week, iso_day = dt.isocalendar()
        days_diff = int(4 - iso_day)
        thursday = dt + pd.DateOffset(days=days_diff)
        month = thursday.month
        week_of_month = (thursday.day - 1) // 7 + 1
        return f"{month}월 {week_of_month}주차"
    except:
        return ""


def classify_flight_time(time_val):
    if pd.isna(time_val):
        return "기타"
    time_str = str(time_val).strip()
    try:
        match = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            total_minutes = hours * 60 + minutes

            t_1000 = 10 * 60
            t_1235 = 12 * 60 + 35
            t_2200 = 22 * 60

            if t_1000 <= total_minutes <= t_1235:
                return "오전(~12:35)"
            elif t_1235 < total_minutes <= t_2200:
                return "오후(12:35~)"
            else:
                return "기타"
        else:
            return "기타"
    except:
        return "기타"


KE_ROUTES = {
    "G/HND", "I/NRT", "I/HND", "P/NRT", "C/NRT", "I/KIX", "G/KIX", "I/UKB",
    "I/OKJ", "I/HIJ", "I/FUK", "I/KOJ", "I/NGS", "I/KMJ", "I/OIT", "I/NGO",
    "P/NGO", "I/KIJ", "I/KMQ", "I/OKA", "I/CTS", "I/AOJ"
}


# 메인 타이틀
st.title("✈️ 주차별 발매 분석 대시보드")

col_up1, col_up2 = st.columns(2)
with col_up1:
    uploaded_file = st.file_uploader(
        "1. RAW DATA 파일 (.xlsx / .csv)", type=["xlsx", "csv"], key="uploader_raw"
    )
    if uploaded_file is not None:
        st.session_state["raw_df"] = load_uploaded_file(uploaded_file.getvalue(), uploaded_file.name)

with col_up2:
    weight_file = st.file_uploader(
        "2. 노선/항공사별 가중치 테이블 파일 (선택 사항)", type=["xlsx", "csv"], key="uploader_weight"
    )
    if weight_file is not None:
        st.session_state["weight_df"] = load_uploaded_file(weight_file.getvalue(), weight_file.name)


if st.session_state["raw_df"] is not None:
    df = st.session_state["raw_df"].copy()

    with st.spinner("데이터 속도를 최적화하는 중입니다..."):
        if "Ticket Purchase Date" in df.columns:
            df["Purchase Week"] = df["Ticket Purchase Date"].apply(get_iso_month_week)
        elif "Purchase Date" in df.columns:
            df["Purchase Week"] = df["Purchase Date"].apply(get_iso_month_week)

        has_origin_cntry = "Trip Origin Country Code" in df.columns
        has_dest_cntry = "Trip Destination Country Code" in df.columns

        if has_origin_cntry and has_dest_cntry:
            def get_bound(row):
                origin = str(row["Trip Origin Country Code"]).strip().upper()
                dest = str(row["Trip Destination Country Code"]).strip().upper()
                if origin == "KR":
                    return "OUT"
                elif dest == "KR":
                    return "IN"
                else:
                    return "기타"

            df["Bound"] = df.apply(get_bound, axis=1)

        if "Flight Departure Time" in df.columns:
            df["Time Slot"] = df["Flight Departure Time"].apply(classify_flight_time)

        orig_code_col = next((c for c in df.columns if "orig" in c.lower() and "cntry" not in c.lower()), None)
        dest_code_col = next((c for c in df.columns if "dest" in c.lower() and "cntry" not in c.lower()), None)

        if has_origin_cntry and has_dest_cntry and orig_code_col and dest_code_col:
            def process_route_and_ke(row):
                orig_cntry = str(row["Trip Origin Country Code"]).strip().upper()
                dest_cntry = str(row["Trip Destination Country Code"]).strip().upper()
                orig_code = str(row[orig_code_col]).strip().upper()
                dest_code = str(row[dest_code_col]).strip().upper()

                if orig_cntry == "KR":
                    kr_code, other_code = orig_code, dest_code
                elif dest_cntry == "KR":
                    kr_code, other_code = dest_code, orig_code
                else:
                    kr_code, other_code = orig_code, dest_code

                if kr_code == "PUS":
                    route_code = f"P/{other_code}"
                elif kr_code == "GMP":
                    route_code = f"G/{other_code}"
                elif kr_code == "CJU":
                    route_code = f"C/{other_code}"
                elif kr_code == "ICN":
                    route_code = f"I/{other_code}"
                else:
                    route_code = other_code

                ke_status = "KE 취항" if route_code in KE_ROUTES else "KE 미취항"
                return pd.Series([route_code, ke_status])

            df[["Route Code", "KE 취항 여부"]] = df.apply(process_route_and_ke, axis=1)

        source_col = next((c for c in df.columns if "source" in c.lower()), None)
        if source_col:
            def classify_sales_channel(val):
                if pd.isna(val):
                    return "간판"
                val_str = str(val).strip().lower()
                if val_str == "direct contributed":
                    return "직판"
                else:
                    return "간판"

            df["Sales Channel"] = df[source_col].apply(classify_sales_channel)

        if "Ticket Travel Month" in df.columns:
            def format_month(val):
                if pd.isna(val):
                    return ""
                try:
                    m = int(float(val))
                    return f"{m:02d}월"
                except:
                    return str(val)
            df["출발월"] = df["Ticket Travel Month"].apply(format_month)

        airline_col = "Dominant Marketing Airline"
        df["Weight"] = 1.0

        if st.session_state["weight_df"] is not None:
            weight_df = st.session_state["weight_df"].copy()
            weight_df.columns = [c.strip() for c in weight_df.columns]

            w_route_col = next((c for c in weight_df.columns if "route" in c.lower()), None)
            w_air_col = next((c for c in weight_df.columns if "air" in c.lower() or "dominant" in c.lower()), None)
            w_val_col = next((c for c in weight_df.columns if "weight" in c.lower() or "가중치" in c.lower() or "multiplier" in c.lower()), None)

            if w_route_col and w_air_col and w_val_col:
                weight_df_sub = weight_df[[w_route_col, w_air_col, w_val_col]].dropna()
                weight_df_sub.columns = ["Route Code", airline_col, "Weight_Val"]
                weight_df_sub["Weight_Val"] = pd.to_numeric(weight_df_sub["Weight_Val"], errors="coerce").fillna(1.0)

                df = df.merge(weight_df_sub, on=["Route Code", airline_col], how="left")
                df["Weight"] = pd.to_numeric(df["Weight_Val"], errors="coerce").fillna(1.0)
                df.drop(columns=["Weight_Val"], inplace=True, errors="ignore")
                st.sidebar.info("💡 가중치 테이블 적용 완료")

        df["Estimated Count"] = pd.to_numeric(df["Weight"], errors="coerce").fillna(1.0)

        # ⚡ 핵심 속도 최적화: 주요 검색 대상 컬럼들을 category 형으로 변환하여 메모리 최소화
        cat_cols = ["KE 취항 여부", "Route Code", "Sales Channel", "Purchase Week", "Bound", "출발월", "Time Slot", airline_col]
        for col in cat_cols:
            if col in df.columns:
                df[col] = df[col].astype("category")

    # ---------------------------------------------------------
    # 🎛️ 사이드바 필터
    # ---------------------------------------------------------
    st.sidebar.header("🎛️ 대시보드 필터")

    filtered_df = df

    if "KE 취항 여부" in df.columns:
        ke_opt = st.sidebar.radio(
            "1. KE 취항 여부",
            ["전체", "KE 취항 노선만", "KE 미취항 노선만"],
            index=1,
        )
        if ke_opt == "KE 취항 노선만":
            filtered_df = filtered_df[filtered_df["KE 취항 여부"] == "KE 취항"]
        elif ke_opt == "KE 미취항 노선만":
            filtered_df = filtered_df[filtered_df["KE 취항 여부"] == "KE 미취항"]

    selected_routes = []
    if "Route Code" in filtered_df.columns:
        route_counts = filtered_df["Route Code"].value_counts()
        ke_routes_sorted = [r for r in route_counts.index if r in KE_ROUTES]
        non_ke_routes_sorted = [r for r in route_counts.index if r not in KE_ROUTES]
        available_routes = ke_routes_sorted + non_ke_routes_sorted

        selected_routes = st.sidebar.multiselect(
            "2. Route Code (노선 선택)",
            options=["전체 (통합 보기)"] + available_routes,
            default=[],
            placeholder="선택 안 함 (전체 통합 보기)",
        )
        if selected_routes and "전체 (통합 보기)" not in selected_routes:
            filtered_df = filtered_df[filtered_df["Route Code"].isin(selected_routes)]
        else:
            selected_routes = []

    if "Sales Channel" in filtered_df.columns:
        channels = sorted([str(x) for x in filtered_df["Sales Channel"].dropna().unique().tolist()])
        selected_channels = st.sidebar.multiselect(
            "3. Sales Channel (직판/간판)",
            options=["전체"] + channels,
            default=[],
            placeholder="선택 안 함 (전체)",
        )
        if selected_channels and "전체" not in selected_channels:
            filtered_df = filtered_df[filtered_df["Sales Channel"].isin(selected_channels)]

    if "Purchase Week" in filtered_df.columns:
        weeks = sorted([str(x) for x in filtered_df["Purchase Week"].dropna().unique().tolist()])
        selected_weeks = st.sidebar.multiselect(
            "4. Purchase Week (구매 주차)",
            options=["전체"] + weeks,
            default=[],
            placeholder="선택 안 함 (전체)",
        )
        if selected_weeks and "전체" not in selected_weeks:
            filtered_df = filtered_df[filtered_df["Purchase Week"].isin(selected_weeks)]

    if "Bound" in filtered_df.columns:
        bounds = sorted([str(x) for x in filtered_df["Bound"].dropna().unique().tolist()])
        selected_bounds = st.sidebar.multiselect(
            "5. Bound (IN/OUT)",
            options=["전체"] + bounds,
            default=[],
            placeholder="선택 안 함 (전체)",
        )
        if selected_bounds and "전체" not in selected_bounds:
            filtered_df = filtered_df[filtered_df["Bound"].isin(selected_bounds)]

    if "출발월" in filtered_df.columns:
        months = sorted([str(x) for x in filtered_df["출발월"].dropna().unique().tolist() if str(x) != ""])
        selected_months = st.sidebar.multiselect(
            "6. 출발월",
            options=["전체"] + months,
            default=[],
            placeholder="선택 안 함 (전체)",
        )
        if selected_months and "전체" not in selected_months:
            filtered_df = filtered_df[filtered_df["출발월"].isin(selected_months)]

    if "Time Slot" in filtered_df.columns:
        slots = sorted([str(x) for x in filtered_df["Time Slot"].dropna().unique().tolist()])
        selected_slots = st.sidebar.multiselect(
            "7. Time Slot (출발 시간대)",
            options=["전체"] + slots,
            default=[],
            placeholder="선택 안 함 (전체)",
        )
        if selected_slots and "전체" not in selected_slots:
            filtered_df = filtered_df[filtered_df["Time Slot"].isin(selected_slots)]

    # ---------------------------------------------------------
    # 📊 메인 화면
    # ---------------------------------------------------------
    st.success(f"✅ 데이터 분석 준비 완료 (적용 건수: {len(filtered_df):,} 건)")

    total_est_count = float(filtered_df["Estimated Count"].sum())

    st.divider()

    st.subheader("🎯 항공사별 발매 점유비 (가중치 추정 반영)")

    if airline_col not in df.columns:
        st.error(f"⚠️ 파일에 `{airline_col}` 컬럼이 존재하지 않습니다. 컬럼명을 확인해주세요.")
    else:
        if len(selected_routes) <= 1:
            if len(selected_routes) == 0:
                chart_title = f"KE 취항 노선 전체 항공사 추정 점유율 (%) (추정 총 {total_est_count:,.1f}건)"
                table_title_pct = "KE 취항 노선 전체 통합 항공사 추정 점유율 (%)"
                table_title_cnt = "KE 취항 노선 전체 통합 항공사 추정 발권 건수 (건)"
            else:
                chart_title = f"[{selected_routes[0]}] 노선 항공사 추정 점유율 (%)"
                table_title_pct = f"[{selected_routes[0]}] 노선 항공사 추정 점유율 (%)"
                table_title_cnt = f"[{selected_routes[0]}] 노선 항공사 추정 발권 건수 (건)"

            est_counts = filtered_df.groupby(airline_col, observed=True)["Estimated Count"].sum().sort_values(ascending=False)
            raw_counts = filtered_df[airline_col].value_counts()

            if est_counts.empty:
                st.warning("선택하신 사이드바 필터 조건에 해당하는 데이터가 없습니다.")
            else:
                pivot_est_full = est_counts.to_frame().T
                pivot_raw_full = raw_counts.to_frame().T

                pivot_pct_full = (pivot_est_full.div(pivot_est_full.sum(axis=1), axis=0) * 100).round(1)

                top_n = 10
                if len(est_counts) > top_n:
                    top_est = est_counts.iloc[:top_n]
                    others_est = est_counts.iloc[top_n:].sum()
                    plot_series = pd.concat([top_est, pd.Series({"기타 (Others)": others_est})])
                else:
                    plot_series = est_counts

                plot_df = plot_series.reset_index()
                plot_df.columns = [airline_col, "추정 발권 건수"]
                plot_df["점유율(%)"] = (plot_df["추정 발권 건수"] / (total_est_count if total_est_count > 0 else 1) * 100).round(1)

                fig = px.bar(
                    plot_df,
                    x="점유율(%)",
                    y=airline_col,
                    orientation="h",
                    title=chart_title,
                    text="점유율(%)",
                    color=airline_col,
                )
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(
                    yaxis=dict(categoryorder="total ascending", title=""),
                    xaxis=dict(title="추정 점유율 (%)", range=[0, min(100, plot_df["점유율(%)"].max() * 1.25)]),
                    height=480,
                    showlegend=False,
                )
                st.plotly_chart(fig, width="stretch")

                tab1, tab2, tab3 = st.tabs(["📊 추정 점유율 (%) 표", "🔢 추정 발권 건수 표", "📋 RAW 실적 건수 표"])
                with tab1:
                    st.subheader(table_title_pct)
                    st.dataframe(pivot_pct_full.map(lambda x: f"{x:.1f}%"), width="stretch")
                with tab2:
                    st.subheader(table_title_cnt)
                    st.dataframe(pivot_est_full.map(lambda x: f"{x:,.1f}"), width="stretch")
                with tab3:
                    st.subheader("RAW 실적 건수 (가중치 미반영)")
                    st.dataframe(pivot_raw_full, width="stretch")

        else:
            chart_title = f"선택한 Route Code별 항공사 추정 점유율 (%)"
            table_title_pct = "선택한 Route Code별 항공사 추정 점유율 (%)"
            table_title_cnt = "선택한 Route Code별 항공사 추정 발권 건수 (건)"

            pivot_est = (
                filtered_df.groupby(["Route Code", airline_col], observed=True)["Estimated Count"]
                .sum()
                .unstack(fill_value=0)
            )

            if pivot_est.empty:
                st.warning("선택하신 사이드바 필터 조건에 해당하는 데이터가 없습니다.")
            else:
                pivot_pct = (pivot_est.div(pivot_est.sum(axis=1), axis=0) * 100).round(1)
                chart_df = pivot_pct.reset_index().melt(id_vars="Route Code", var_name=airline_col, value_name="점유율(%)")

                fig = px.bar(
                    chart_df,
                    x="Route Code",
                    y="점유율(%)",
                    color=airline_col,
                    title=chart_title,
                    text="점유율(%)",
                    barmode="stack",
                )
                fig.update_traces(texttemplate="%{text}%", textposition="inside")
                fig.update_layout(yaxis=dict(title="추정 점유율 (%)", range=[0, 100]), xaxis_title="", height=500)
                st.plotly_chart(fig, width="stretch")

                tab1, tab2 = st.tabs(["📊 추정 점유율 (%) 표", "🔢 추정 발권 건수 표"])
                with tab1:
                    st.subheader(table_title_pct)
                    st.dataframe(pivot_pct.map(lambda x: f"{x:.1f}%"), width="stretch")
                with tab2:
                    st.subheader(table_title_cnt)
                    st.dataframe(pivot_est.map(lambda x: f"{x:,.1f}"), width="stretch")

    st.divider()

    st.subheader("🍕 세부 비중 분석 (Sales Channel & Bound)")
    
    col_pie1, col_pie2 = st.columns(2)

    with col_pie1:
        if "Sales Channel" in filtered_df.columns:
            sc_df = filtered_df.groupby("Sales Channel", observed=True)["Estimated Count"].sum().reset_index()
            fig_sc = px.pie(
                sc_df,
                values="Estimated Count",
                names="Sales Channel",
                title="<b>Sales Channel별 추정 비중</b>",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_sc.update_traces(textinfo="label+percent", textfont_size=13)
            fig_sc.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig_sc, width="stretch")

    with col_pie2:
        if "Bound" in filtered_df.columns:
            bound_df = filtered_df.groupby("Bound", observed=True)["Estimated Count"].sum().reset_index()
            fig_bound = px.pie(
                bound_df,
                values="Estimated Count",
                names="Bound",
                title="<b>Bound(IN/OUT)별 추정 비중</b>",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_bound.update_traces(textinfo="label+percent", textfont_size=13)
            fig_bound.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig_bound, width="stretch")

    st.divider()

    st.subheader("📋 가공 완료 데이터 미리보기 (가중치 및 추정건수 포함)")
    new_cols = [
        c
        for c in [
            "Route Code",
            "KE 취항 여부",
            "Sales Channel",
            "출발월",
            "Weight",
            "Estimated Count",
            "Purchase Week",
            "Bound",
            "Time Slot",
        ]
        if c in filtered_df.columns
    ]
    other_cols = [c for c in filtered_df.columns if c not in new_cols]
    final_df = filtered_df[new_cols + other_cols]

    st.dataframe(final_df.head(30), width="stretch")
    st.caption("※ 대시보드 속도 향상을 위해 미리보기는 상위 30건만 표출되며, 전체 데이터는 아래 엑셀 다운로드 버튼을 이용하세요.")

    st.subheader("📥 필터 및 추정 반영 데이터 엑셀 다운로드")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Processed_Ticketing")
    processed_data = output.getvalue()

    st.download_button(
        label="🚀 가공 및 필터 완료 엑셀 파일 다운로드",
        data=processed_data,
        file_name="processed_ticketing_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("👋 분석을 시작하려면 상단의 '1. RAW DATA 파일'을 업로드해 주세요.")