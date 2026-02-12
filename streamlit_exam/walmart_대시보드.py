# streamlit_walmart_dashboard_ko.py
# Run: streamlit run streamlit_walmart_dashboard_ko.py
#
# ✅ 원본 CSV는 그대로 두고
#   - (1) 컬럼명이 한국어/영어 어떤 버전이든 자동 인식
#   - (2) 화면(UI/차트)에서는 값까지 한국어로 표시
#   - (3) 내부 계산/필터/통계는 표준(영문) 컬럼으로 안정적으로 수행

import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
from itertools import combinations
import plotly.express as px

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Walmart 구매 데이터 | Insight Cockpit",
    page_icon="🧭",
    layout="wide",
)

st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
div[data-testid="metric-container"]{
    border: 1px solid rgba(49, 51, 63, 0.15);
    border-radius: 14px;
    padding: 14px 14px 10px 14px;
    background: rgba(255,255,255,0.02);
}
.small-note {opacity: 0.75; font-size: 0.92rem;}
.badge {display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid rgba(49,51,63,0.25); font-size:0.85rem; margin-right:6px;}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Canonical orders (internal)
# -----------------------------
AGE_ORDER = ["0-17", "18-25", "26-35", "36-45", "46-50", "51-55", "55+"]
STAY_ORDER = ["0", "1", "2", "3", "4+"]
CITY_ORDER = ["A", "B", "C"]

# -----------------------------
# Column name mapping
# -----------------------------
CANON_TO_KO_COL = {
    "User_ID": "고객ID",
    "Product_ID": "상품ID",
    "Gender": "성별",
    "Age": "연령대",
    "Occupation": "직업코드",
    "City_Category": "도시유형",
    "Stay_In_Current_City_Years": "현도시거주기간",
    "Marital_Status": "결혼여부",
    "Product_Category": "제품카테고리",
    "Purchase": "구매금액",
}
KO_TO_CANON_COL = {v: k for k, v in CANON_TO_KO_COL.items()}

# -----------------------------
# Value mapping (display only)
# -----------------------------
GENDER_MAP = {"M": "남", "F": "여"}
CITY_MAP = {"A": "도시유형 A", "B": "도시유형 B", "C": "도시유형 C"}
AGE_MAP = {
    "0-17": "0-17세",
    "18-25": "18-25세",
    "26-35": "26-35세",
    "36-45": "36-45세",
    "46-50": "46-50세",
    "51-55": "51-55세",
    "55+": "55세+",
}
STAY_MAP = {"0": "0년", "1": "1년", "2": "2년", "3": "3년", "4+": "4년+"}
MARITAL_MAP = {0: "미혼", 1: "기혼"}  # ⚠️ 일반적인 해석(데이터셋 관례). 필요하면 아래에서 바꾸세요.

AGE_ORDER_KO = [AGE_MAP[a] for a in AGE_ORDER]
STAY_ORDER_KO = [STAY_MAP[s] for s in STAY_ORDER]
CITY_ORDER_KO = [CITY_MAP[c] for c in CITY_ORDER]


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """한국어/영어 컬럼명을 모두 받아 내부 표준(영문) 컬럼으로 맞춤."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    rename_map = {c: KO_TO_CANON_COL[c] for c in df.columns if c in KO_TO_CANON_COL}
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def val_to_ko(col: str, v):
    """내부 값 -> 화면 표시용 한국어 값."""
    if col == "Gender":
        return GENDER_MAP.get(v, str(v))
    if col == "City_Category":
        return CITY_MAP.get(v, str(v))
    if col == "Age":
        return AGE_MAP.get(v, str(v))
    if col == "Stay_In_Current_City_Years":
        return STAY_MAP.get(str(v), str(v))
    if col == "Marital_Status":
        try:
            vv = int(v)
        except Exception:
            vv = v
        return MARITAL_MAP.get(vv, str(v))
    if col == "Occupation":
        return f"직업 {v}"
    if col == "Product_Category":
        return f"카테고리 {v}"
    return str(v)


def to_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """표시용 DF(한국어 컬럼명 + 값 한국어화). 원본/분석용 DF는 건드리지 않음."""
    d = df.copy()

    if "Gender" in d.columns:
        d["Gender"] = d["Gender"].map(GENDER_MAP).fillna(d["Gender"].astype(str))

    if "City_Category" in d.columns:
        d["City_Category"] = d["City_Category"].astype(str).map(CITY_MAP).fillna(d["City_Category"].astype(str))

    if "Age" in d.columns:
        d["Age"] = d["Age"].astype(str).map(AGE_MAP).fillna(d["Age"].astype(str))

    if "Stay_In_Current_City_Years" in d.columns:
        d["Stay_In_Current_City_Years"] = d["Stay_In_Current_City_Years"].astype(str).map(STAY_MAP).fillna(
            d["Stay_In_Current_City_Years"].astype(str)
        )

    if "Marital_Status" in d.columns:
        d["Marital_Status"] = d["Marital_Status"].map(MARITAL_MAP).fillna(d["Marital_Status"].astype(str))

    if "Occupation" in d.columns:
        d["Occupation"] = d["Occupation"].astype(str).map(lambda x: f"직업 {x}")

    if "Product_Category" in d.columns:
        d["Product_Category"] = d["Product_Category"].astype(str).map(lambda x: f"카테고리 {x}")

    # rename columns
    d = d.rename(columns=CANON_TO_KO_COL)

    # keep nice ordering
    if "연령대" in d.columns:
        d["연령대"] = pd.Categorical(d["연령대"], categories=AGE_ORDER_KO, ordered=True)
    if "현도시거주기간" in d.columns:
        d["현도시거주기간"] = pd.Categorical(d["현도시거주기간"], categories=STAY_ORDER_KO, ordered=True)
    if "도시유형" in d.columns:
        d["도시유형"] = pd.Categorical(d["도시유형"], categories=CITY_ORDER_KO, ordered=True)

    return d


# -----------------------------
# Data load
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data_from_path(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = standardize_columns(df)

    # Normalize dtypes/orders (internal)
    if "Age" in df.columns:
        df["Age"] = pd.Categorical(df["Age"].astype(str), categories=AGE_ORDER, ordered=True)

    if "Stay_In_Current_City_Years" in df.columns:
        df["Stay_In_Current_City_Years"] = pd.Categorical(
            df["Stay_In_Current_City_Years"].astype(str), categories=STAY_ORDER, ordered=True
        )

    if "City_Category" in df.columns:
        df["City_Category"] = pd.Categorical(df["City_Category"].astype(str), categories=CITY_ORDER, ordered=True)

    # Keep masked numeric categories as int
    for c in ["Occupation", "Product_Category", "Marital_Status"]:
        if c in df.columns:
            df[c] = df[c].astype("int64")

    return df


def apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    out = df
    if f["city"]:
        out = out[out["City_Category"].isin(f["city"])]
    if f["gender"]:
        out = out[out["Gender"].isin(f["gender"])]
    if f["age"]:
        out = out[out["Age"].isin(f["age"])]
    if f["stay"]:
        out = out[out["Stay_In_Current_City_Years"].isin(f["stay"])]
    if f["marital"]:
        out = out[out["Marital_Status"].isin(f["marital"])]
    if f["occupation"]:
        out = out[out["Occupation"].isin(f["occupation"])]
    if f["prodcat"]:
        out = out[out["Product_Category"].isin(f["prodcat"])]

    pr_min, pr_max = f["purchase_range"]
    out = out[(out["Purchase"] >= pr_min) & (out["Purchase"] <= pr_max)]
    return out


# -----------------------------
# Stats helpers
# -----------------------------
def epsilon_squared_kw(H: float, k: int, n: int) -> float:
    if n <= k:
        return np.nan
    return float(max(0.0, (H - k + 1.0) / (n - k)))


def kruskal_with_eps2(df: pd.DataFrame, group_col: str, value_col: str = "Purchase"):
    groups = []
    labels = []
    for g, sub in df.groupby(group_col, observed=True):
        vals = sub[value_col].dropna().values
        if len(vals) >= 2:
            groups.append(vals)
            labels.append(g)

    k = len(groups)
    n = int(sum(len(x) for x in groups))
    if k < 2:
        return None

    H, p = stats.kruskal(*groups)
    eps2 = epsilon_squared_kw(H, k, n)
    return {"H": float(H), "p": float(p), "eps2": float(eps2), "k": k, "n": n, "labels": labels}


def effect_badge(value: float, kind: str = "eps2") -> str:
    if np.isnan(value):
        return "N/A"
    if kind == "eps2":
        if value < 0.01:
            return "signal: tiny"
        if value < 0.06:
            return "signal: small"
        if value < 0.14:
            return "signal: medium"
        return "signal: large"
    if value < 0.10:
        return "signal: tiny"
    if value < 0.30:
        return "signal: small"
    if value < 0.50:
        return "signal: medium"
    return "signal: large"


def cramers_v_from_crosstab(ct: pd.DataFrame) -> dict:
    chi2, p, dof, exp = stats.chi2_contingency(ct.values, correction=False)
    n = ct.values.sum()
    r, c = ct.shape
    denom = n * max(1, (min(r - 1, c - 1)))
    v = np.sqrt(chi2 / denom) if denom > 0 else np.nan
    return {"chi2": float(chi2), "p": float(p), "dof": int(dof), "v": float(v), "n": int(n)}


def mannwhitney_pairwise(df: pd.DataFrame, group_col: str, value_col: str = "Purchase"):
    cats = [c for c in df[group_col].dropna().unique()]
    cats = sorted(cats, key=lambda x: str(x))
    pairs = list(combinations(cats, 2))
    m = len(pairs)
    rows = []

    for a, b in pairs:
        xa = df.loc[df[group_col] == a, value_col].dropna().values
        xb = df.loc[df[group_col] == b, value_col].dropna().values
        if len(xa) < 2 or len(xb) < 2:
            continue
        U, p = stats.mannwhitneyu(xa, xb, alternative="two-sided")
        p_bonf = min(p * m, 1.0)
        rows.append(
            {
                "비교": f"{val_to_ko(group_col, a)} vs {val_to_ko(group_col, b)}",
                "U": float(U),
                "p_raw": float(p),
                "p_bonf": float(p_bonf),
            }
        )

    return pd.DataFrame(rows).sort_values("p_bonf", ascending=True)


def ecdf_df(x: np.ndarray) -> pd.DataFrame:
    x = np.asarray(x)
    x = x[~np.isnan(x)]
    x = np.sort(x)
    y = np.arange(1, len(x) + 1) / len(x) if len(x) else np.array([])
    return pd.DataFrame({"x": x, "y": y})


@st.cache_data(show_spinner=False)
def signal_scoreboard(df: pd.DataFrame, sample_n: int = 120_000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    if len(df) > sample_n:
        idx = rng.choice(len(df), size=sample_n, replace=False)
        d = df.iloc[idx].copy()
    else:
        d = df.copy()

    cols = ["City_Category", "Gender", "Age", "Stay_In_Current_City_Years", "Marital_Status", "Occupation", "Product_Category"]
    rows = []
    for c in cols:
        if c not in d.columns:
            continue
        res = kruskal_with_eps2(d, c, "Purchase")
        if res is None:
            continue
        rows.append(
            {
                "변수": CANON_TO_KO_COL.get(c, c),
                "표본수(n)": res["n"],
                "그룹수(k)": res["k"],
                "H": res["H"],
                "p-value": res["p"],
                "효과크기(ε²)": res["eps2"],
                "signal": effect_badge(res["eps2"], "eps2"),
            }
        )

    return pd.DataFrame(rows).sort_values("효과크기(ε²)", ascending=False)


def top3_groups(df: pd.DataFrame, group_col: str, value_col: str = "Purchase") -> pd.DataFrame:
    g = (
        df.groupby(group_col, observed=True)[value_col]
        .agg(count="size", mean="mean", median="median")
        .reset_index()
    )
    g["mean"] = g["mean"].round(2)
    g["median"] = g["median"].round(2)
    return g.sort_values(["mean", "count"], ascending=[False, False])


# -----------------------------
# Sidebar: load + filter
# -----------------------------
st.title("🧭 Walmart 구매 데이터 Insight Cockpit")

with st.sidebar:
    st.header("⚙️ 데이터 & 필터")

    uploaded = st.file_uploader("CSV 업로드 (없으면 기본 walmart.csv 사용)", type=["csv"])
    default_path = "walmart.csv"

    if uploaded is not None:
        df_raw = pd.read_csv(uploaded)
        df_raw = standardize_columns(df_raw)
        # mirror preprocessing
        if "Age" in df_raw.columns:
            df_raw["Age"] = pd.Categorical(df_raw["Age"].astype(str), categories=AGE_ORDER, ordered=True)
        if "Stay_In_Current_City_Years" in df_raw.columns:
            df_raw["Stay_In_Current_City_Years"] = pd.Categorical(
                df_raw["Stay_In_Current_City_Years"].astype(str), categories=STAY_ORDER, ordered=True
            )
        if "City_Category" in df_raw.columns:
            df_raw["City_Category"] = pd.Categorical(df_raw["City_Category"].astype(str), categories=CITY_ORDER, ordered=True)

        for c in ["Occupation", "Product_Category", "Marital_Status"]:
            if c in df_raw.columns:
                df_raw[c] = df_raw[c].astype("int64")
    else:
        df_raw = load_data_from_path(default_path)

    st.markdown('<div class="small-note">필터는 "지금 보고 있는 세그먼트" 기준으로 통계/차트를 다시 계산해요.</div>', unsafe_allow_html=True)

    # Filters: options are canonical values, but shown as Korean via format_func
    city = st.multiselect(
        "도시유형",
        options=list(df_raw["City_Category"].cat.categories),
        default=[],
        format_func=lambda x: val_to_ko("City_Category", x),
    )
    gender = st.multiselect(
        "성별",
        options=sorted(df_raw["Gender"].unique()),
        default=[],
        format_func=lambda x: val_to_ko("Gender", x),
    )
    age = st.multiselect(
        "연령대",
        options=list(df_raw["Age"].cat.categories),
        default=[],
        format_func=lambda x: val_to_ko("Age", x),
    )
    stay = st.multiselect(
        "현도시거주기간",
        options=list(df_raw["Stay_In_Current_City_Years"].cat.categories),
        default=[],
        format_func=lambda x: val_to_ko("Stay_In_Current_City_Years", x),
    )

    marital = st.multiselect(
        "결혼여부",
        options=sorted(df_raw["Marital_Status"].unique()),
        default=[],
        format_func=lambda x: val_to_ko("Marital_Status", x),
    )
    occupation = st.multiselect(
        "직업코드",
        options=sorted(df_raw["Occupation"].unique()),
        default=[],
        format_func=lambda x: val_to_ko("Occupation", x),
    )
    prodcat = st.multiselect(
        "제품카테고리",
        options=sorted(df_raw["Product_Category"].unique()),
        default=[],
        format_func=lambda x: val_to_ko("Product_Category", x),
    )

    pr_min = int(df_raw["Purchase"].min())
    pr_max = int(df_raw["Purchase"].max())
    purchase_range = st.slider("구매금액 범위", min_value=pr_min, max_value=pr_max, value=(pr_min, pr_max))

    filters = dict(
        city=city,
        gender=gender,
        age=age,
        stay=stay,
        marital=marital,
        occupation=occupation,
        prodcat=prodcat,
        purchase_range=purchase_range,
    )

df = apply_filters(df_raw, filters)
df_disp = to_display_df(df)  # charts/UI용

# -----------------------------
# Top ribbon: quick status
# -----------------------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("거래 수", f"{len(df):,}")
kpi2.metric("고객 수", f"{df['User_ID'].nunique():,}")
kpi3.metric("상품 수", f"{df['Product_ID'].nunique():,}")
kpi4.metric("총 구매금액", f"{int(df['Purchase'].sum()):,}")
kpi5.metric("평균 구매금액", f"{df['Purchase'].mean():,.1f}")

st.markdown(
    f"""
<span class="badge">현재 뷰</span>
<span class="small-note">필터 적용 후 표본: <b>{len(df):,}</b> rows</span>
""",
    unsafe_allow_html=True,
)

tabs = st.tabs(["🎛️ 한눈에 보기", "🧪 가설 탐험", "🧩 조합 히트맵", "🔎 세그먼트 TOP3"])

# -----------------------------
# Tab 1: Overview
# -----------------------------
with tabs[0]:
    left, right = st.columns([1.25, 1])

    with left:
        st.subheader("구매금액 분포 (빠른 감 잡기)")
        logx = st.toggle("로그 스케일(구매금액)", value=False)
        fig = px.histogram(df_disp, x="구매금액", nbins=70, marginal="box")
        if logx:
            fig.update_xaxes(type="log")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("필터된 데이터 다운로드"):
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "CSV 다운로드(원본 컬럼/값)",
                    data=df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="walmart_filtered_raw.csv",
                    mime="text/csv",
                )
            with c2:
                st.download_button(
                    "CSV 다운로드(한국어 컬럼/값)",
                    data=df_disp.to_csv(index=False).encode("utf-8-sig"),
                    file_name="walmart_filtered_ko.csv",
                    mime="text/csv",
                )

    with right:
        st.subheader("Signal Scoreboard 🏁")
        st.caption("표본이 크면 p-value는 거의 항상 작아져요. 그래서 '효과크기(ε²)'로 변수별 영향력을 한 번에 봅니다.")

        sample_n = st.slider("Scoreboard 표본 크기", 30_000, 200_000, 120_000, step=10_000)
        board = signal_scoreboard(df, sample_n=sample_n)

        if len(board):
            st.dataframe(board, use_container_width=True, hide_index=True)

            fig2 = px.bar(
                board.sort_values("효과크기(ε²)", ascending=True),
                x="효과크기(ε²)",
                y="변수",
                orientation="h",
                hover_data=["표본수(n)", "그룹수(k)", "p-value", "signal"],
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("필터 때문에 그룹이 1개만 남았거나 표본이 너무 작아요. 필터를 조금 풀어보세요.")

    st.divider()
    st.subheader("한 줄 인사이트 생성기 ✍️")
    c1, c2 = st.columns([1, 1])
    with c1:
        focus = st.selectbox(
            "어느 변수를 한 문장으로 요약할까?",
            ["City_Category", "Stay_In_Current_City_Years", "Product_Category", "Gender", "Age", "Occupation", "Marital_Status"],
            format_func=lambda x: CANON_TO_KO_COL.get(x, x),
        )
    with c2:
        mode = st.selectbox("기준", ["mean(평균)", "median(중앙값)"])

    g = top3_groups(df, focus)
    if len(g):
        g2 = g.copy()
        g2[focus] = g2[focus].apply(lambda v: val_to_ko(focus, v))
        top = g2.iloc[0]
        basis = "mean" if "mean" in mode else "median"
        val = float(top[basis])
        st.success(
            f"현재 필터 기준으로 **{CANON_TO_KO_COL.get(focus, focus)}={top[focus]}** 그룹이 {mode} 기준으로 가장 높아요 "
            f"(count={int(top['count']):,}, {mode.split('(')[0]}={val:,.1f})."
        )
        st.caption("이 문장을 그대로 발표/보고서에 박아도 자연스럽게 돌아가게 만든 문장 템플릿이에요 🙂")

# -----------------------------
# Tab 2: Hypotheses explorer
# -----------------------------
with tabs[1]:
    st.subheader("가설 탐험 모드")
    st.caption("3가지 가설을 스위치로 왔다 갔다 하면서, 차트+검정+효과크기를 한 화면에 묶었습니다.")

    h = st.radio(
        "가설 선택",
        ["가설 1: 도시유형별 구매금액 차이", "가설 2: 거주기간별 구매금액 차이", "가설 3: 제품카테고리와 고객특성(성별/연령) 연관"],
        horizontal=True,
    )

    if h.startswith("가설 1"):
        st.markdown("**질문:** 도시유형(A/B/C)에 따라 구매금액 분포가 달라질까?")
        a, b = st.columns([1.1, 0.9])

        with a:
            fig = px.box(df_disp, x="도시유형", y="구매금액", points=False)
            st.plotly_chart(fig, use_container_width=True)

            # ECDF: compute from canonical but label in KO
            ecdfs = []
            for c in df["City_Category"].dropna().unique():
                ecdf = ecdf_df(df.loc[df["City_Category"] == c, "Purchase"].values)
                ecdf["도시유형"] = val_to_ko("City_Category", c)
                ecdfs.append(ecdf)
            if ecdfs:
                fig_ecdf = px.line(pd.concat(ecdfs, ignore_index=True), x="x", y="y", color="도시유형")
                fig_ecdf.update_layout(xaxis_title="구매금액", yaxis_title="누적비율(ECDF)")
                st.plotly_chart(fig_ecdf, use_container_width=True)

        with b:
            res = kruskal_with_eps2(df, "City_Category")
            if res is None:
                st.info("그룹이 2개 이상 필요해요. 필터를 조정해보세요.")
            else:
                st.markdown(
                    f"""
- Kruskal-Wallis H = **{res['H']:.3f}**
- p-value = **{res['p']:.3e}**
- 효과크기 ε² = **{res['eps2']:.6f}**  → **{effect_badge(res['eps2'], 'eps2')}**
"""
                )
                st.caption("p-value가 작아도 ε²가 작으면 '실무적 차이는 작다'로 해석하는 게 자연스럽습니다.")

                if st.button("도시유형 사후검정 (Mann-Whitney + Bonferroni) 실행"):
                    pw = mannwhitney_pairwise(df, "City_Category")
                    st.dataframe(pw, use_container_width=True, hide_index=True)

    elif h.startswith("가설 2"):
        st.markdown("**질문:** 현 도시 거주기간에 따라 구매금액 특성이 달라질까?")
        a, b = st.columns([1.1, 0.9])

        with a:
            fig = px.box(df_disp, x="현도시거주기간", y="구매금액", points=False)
            st.plotly_chart(fig, use_container_width=True)

        with b:
            res = kruskal_with_eps2(df, "Stay_In_Current_City_Years")
            if res is None:
                st.info("그룹이 2개 이상 필요해요. 필터를 조정해보세요.")
            else:
                st.markdown(
                    f"""
- Kruskal-Wallis H = **{res['H']:.3f}**
- p-value = **{res['p']:.3e}**
- 효과크기 ε² = **{res['eps2']:.6f}**  → **{effect_badge(res['eps2'], 'eps2')}**
"""
                )

            # Spearman trend (ordinal mapping)
            stay_map = {k: i for i, k in enumerate(STAY_ORDER)}
            x = df["Stay_In_Current_City_Years"].astype(str).map(stay_map)
            rho, p_rho = stats.spearmanr(x, df["Purchase"].values, nan_policy="omit")
            st.markdown(f"- 단조 경향(Spearman ρ) = **{rho:.4f}** (p={p_rho:.3e})")

            # Variance difference (Levene median)
            groups = [sub["Purchase"].values for _, sub in df.groupby("Stay_In_Current_City_Years", observed=True)]
            if len(groups) >= 2:
                lev_stat, lev_p = stats.levene(*groups, center="median")
                st.markdown(f"- 분산 차이(Levene, median) = **{lev_stat:.3f}** (p={lev_p:.3e})")

    else:
        st.markdown("**질문:** 제품카테고리 분포가 성별/연령에 편중되어 있을까?")
        a, b = st.columns(2)

        with a:
            st.markdown("### 3-A. 제품카테고리 × 성별")
            ct = pd.crosstab(df["Product_Category"], df["Gender"])
            res = cramers_v_from_crosstab(ct)

            st.markdown(
                f"""
- χ² = **{res['chi2']:.2f}**, dof={res['dof']}, p={res['p']:.3e}  
- Cramer's V = **{res['v']:.4f}** → **{effect_badge(res['v'], 'v')}**
"""
            )

            # ratio chart (display labels)
            ct_disp = ct.copy()
            ct_disp.index = ct_disp.index.map(lambda x: val_to_ko("Product_Category", x))
            ct_disp.columns = ct_disp.columns.map(lambda x: val_to_ko("Gender", x))

            tmp_ratio = ct_disp.div(ct_disp.sum(axis=1), axis=0).reset_index()
            id_col = tmp_ratio.columns[0]  # 'Product_Category' or 'index' depending on index name
            ratio = tmp_ratio.melt(id_vars=id_col, var_name="성별", value_name="비율")
            ratio = ratio.rename(columns={id_col: "제품카테고리"})

            fig = px.bar(ratio, x="제품카테고리", y="비율", color="성별", barmode="group")
            fig.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)

        with b:
            st.markdown("### 3-B. 제품카테고리 × 연령대")
            ct2 = pd.crosstab(df["Product_Category"], df["Age"])
            res2 = cramers_v_from_crosstab(ct2)

            st.markdown(
                f"""
- χ² = **{res2['chi2']:.2f}**, dof={res2['dof']}, p={res2['p']:.3e}  
- Cramer's V = **{res2['v']:.4f}** → **{effect_badge(res2['v'], 'v')}**
"""
            )

            ct2_disp = ct2.copy()
            ct2_disp.index = ct2_disp.index.map(lambda x: val_to_ko("Product_Category", x))
            ct2_disp.columns = ct2_disp.columns.map(lambda x: val_to_ko("Age", x))

            tmp_ratio2 = ct2_disp.div(ct2_disp.sum(axis=1), axis=0).reset_index()
            id_col2 = tmp_ratio2.columns[0]  # 'Product_Category' or 'index'
            ratio2 = tmp_ratio2.melt(id_vars=id_col2, var_name="연령대", value_name="비율")
            ratio2 = ratio2.rename(columns={id_col2: "제품카테고리"})

            fig2 = px.line(ratio2, x="연령대", y="비율", color="제품카테고리", markers=False)
            fig2.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Tab 3: Cross heatmap
# -----------------------------
with tabs[2]:
    st.subheader("도시유형 × 제품카테고리 평균 구매금액 히트맵")
    st.caption("교차 세그먼트 느낌을 그대로 가져오되, 필터로 즉시 재계산되는 버전입니다.")

    pivot = pd.pivot_table(
        df_disp,
        values="구매금액",
        index="도시유형",
        columns="제품카테고리",
        aggfunc="mean",
        observed=True,
    )

    fig = px.imshow(pivot, aspect="auto", origin="lower")
    fig.update_layout(xaxis_title="제품카테고리", yaxis_title="도시유형")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("이 조합에서 '튀는' 셀 찾기 (Top N)"):
        n_top = st.slider("Top N", 5, 30, 10)
        tmp = pivot.stack().reset_index()
        tmp.columns = ["도시유형", "제품카테고리", "평균구매금액"]
        tmp = tmp.sort_values("평균구매금액", ascending=False).head(n_top)
        tmp["평균구매금액"] = tmp["평균구매금액"].round(1)
        st.dataframe(tmp, use_container_width=True, hide_index=True)

# -----------------------------
# Tab 4: Segment top3
# -----------------------------
with tabs[3]:
    st.subheader("세그먼트 TOP3 (mean/median + count 같이 보기)")
    st.caption("그룹별 TOP3를 대시보드용으로 재현했어요.")

    col1, col2 = st.columns([1, 1])
    with col1:
        target_col = st.selectbox(
            "그룹 변수 선택",
            ["Gender", "Age", "City_Category", "Stay_In_Current_City_Years", "Marital_Status", "Occupation", "Product_Category"],
            format_func=lambda x: CANON_TO_KO_COL.get(x, x),
        )
    with col2:
        sort_by = st.selectbox("정렬 기준", ["mean", "median"])

    g = top3_groups(df, target_col)
    if len(g) == 0:
        st.info("표본이 부족해서 계산이 어려워요. 필터를 조금 풀어보세요.")
    else:
        g2 = g.copy()
        g2[target_col] = g2[target_col].apply(lambda v: val_to_ko(target_col, v))

        g_sorted = g2.sort_values([sort_by, "count"], ascending=[False, False])
        st.dataframe(g_sorted.head(15), use_container_width=True, hide_index=True)

        top3 = g_sorted.head(3).copy()
        st.markdown("### TOP3 요약")
        for _, row in top3.iterrows():
            st.write(
                f"- {CANON_TO_KO_COL.get(target_col, target_col)} **{row[target_col]}** | "
                f"count={int(row['count']):,} | mean={row['mean']:,.1f} | median={row['median']:,.1f}"
            )

st.markdown(
    "<div class='small-note'>Tip: 필터를 과하게 걸면 그룹이 1개만 남아 검정이 불가능해요. "
    "그럴 때는 (1) 범주형 필터를 줄이거나 (2) 구매금액 범위를 넓혀보세요.</div>",
    unsafe_allow_html=True,
)
