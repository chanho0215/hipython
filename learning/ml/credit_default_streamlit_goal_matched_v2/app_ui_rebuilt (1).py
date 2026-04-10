import traceback
import time
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="신용카드 연체확률 예측 시스템",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
    .stApp {
        background: #f7f8fb;
    }
    .main .block-container {
        max-width: 1240px;
        padding-top: 2.1rem;
        padding-bottom: 2.2rem;
    }
    [data-testid="stSidebar"] {
        background: #eef1f6;
        border-right: 1px solid #dde3ec;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.8rem;
        padding-left: 0.85rem;
        padding-right: 0.85rem;
        padding-bottom: 1.2rem;
    }
    [data-testid="stSidebar"] label {
        font-size: 0.9rem !important;
        color: #536072 !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .stNumberInput, 
    [data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 0.55rem;
    }
    [data-testid="stSidebar"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        border-radius: 12px !important;
        border: 1px solid #dde3ec !important;
        background: rgba(255,255,255,0.78) !important;
        min-height: 44px;
    }
    .title-wrap {
        margin-bottom: 0.15rem;
    }
    .app-title {
        font-size: 3.05rem;
        line-height: 1.1;
        font-weight: 900;
        color: #202739;
        letter-spacing: -0.03em;
        margin: 0;
    }
    .app-subtitle {
        margin-top: 0.7rem;
        color: #7e8796;
        font-size: 1.02rem;
        font-weight: 500;
    }
    .top-rule {
        margin-top: 1.6rem;
        margin-bottom: 1.95rem;
        border-top: 1px solid #d9dee7;
    }
    .plain-metric-label {
        color: #4b5565;
        font-size: 0.92rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .plain-metric-value {
        color: #212939;
        font-size: 3.0rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    .risk-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: #ffe7ea;
        color: #e06666;
        border-radius: 999px;
        padding: 0.22rem 0.55rem;
        font-size: 0.86rem;
        font-weight: 700;
    }
    .risk-card {
        min-height: 150px;
        border-radius: 16px;
        padding: 1.1rem 1.25rem 0.95rem 1.25rem;
        background: #e8f6ed;
        border-left: 5px solid #2fbe63;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
    }
    .risk-bubble {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        margin: 0 auto 0.55rem auto;
        background: radial-gradient(circle at 30% 30%, #95f0b0 0%, #58cf87 45%, #34b46d 70%, #25995b 100%);
        box-shadow: 0 4px 14px rgba(53, 185, 102, 0.35);
    }
    .risk-name {
        text-align: center;
        font-size: 2.25rem;
        font-weight: 900;
        color: #2faa61;
        line-height: 1.1;
    }
    .risk-caption {
        text-align: center;
        color: #7f8b98;
        font-size: 0.95rem;
        margin-top: 0.55rem;
        font-weight: 600;
    }
    .action-card {
        min-height: 86px;
        border-radius: 14px;
        padding: 1.0rem 1.15rem;
        background: #e8f6ed;
        border-left: 4px solid #32bf67;
    }
    .action-label {
        color: #5f6c79;
        font-size: 0.9rem;
        font-weight: 700;
    }
    .action-value {
        color: #2faa61;
        font-size: 1.95rem;
        font-weight: 850;
        margin-top: 0.5rem;
        line-height: 1.2;
    }
    .section-head {
        color: #27303f;
        font-size: 1.45rem;
        font-weight: 900;
        margin: 0 0 0.35rem 0;
    }
    .section-kicker {
        color: #364152;
        font-size: 1.05rem;
        font-weight: 800;
        margin-bottom: 0.55rem;
    }
    .input-title {
        color: #27303f;
        font-size: 1.2rem;
        font-weight: 900;
        margin-bottom: 0.2rem;
    }
    .chip-row {
        display: flex;
        gap: 0.7rem;
        flex-wrap: wrap;
        margin-top: 0.25rem;
        margin-bottom: 0.2rem;
    }
    .chip {
        background: #fff;
        border: 1px solid #d8dde6;
        border-radius: 999px;
        padding: 0.42rem 0.82rem;
        font-size: 0.88rem;
        font-weight: 800;
        color: #364152;
    }
    .sidebar-group {
        color: #263042;
        font-size: 1.1rem;
        font-weight: 900;
        margin-top: 0.8rem;
        margin-bottom: 0.65rem;
    }
    .sidebar-note {
        color: #7b8696;
        font-size: 0.78rem;
        margin-top: -0.2rem;
        margin-bottom: 0.45rem;
    }
    .summary-wrap {
        margin-top: 0.35rem;
    }
    .footer-caption {
        color: #7f8796;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .stButton > button {
        border-radius: 12px !important;
        background: #ff5257 !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        height: 46px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 0.55rem 0.9rem;
        font-weight: 800;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

MODEL_CANDIDATES = [
    "credit_pipeline.pkl",
    "artifacts/credit_pipeline.pkl",
    "artifacts/credit_default_core_pca_rf_pipeline.pkl",
]

FEATURE_ORDER = [
    "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE",
    "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
    "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
    "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
]

SEX_MAP = {"남": 1, "여": 2}
EDU_MAP = {"대학원": 1, "대학": 2, "고졸": 3}
MARRIAGE_MAP = {"기혼": 1, "미혼": 2, "기타": 3}
PAY_MAP = {
    "정상(-1)": -1, "0개월": 0, "1개월": 1, "2개월": 2, "3개월": 3,
    "4개월": 4, "5개월": 5, "6개월": 6, "7개월": 7, "8개월": 8, "9개월": 9
}

KR_LABELS = {
    "LIMIT_BAL": "신용 한도", "SEX": "성별", "EDUCATION": "학력", "MARRIAGE": "혼인 상태", "AGE": "나이",
    "PAY_0": "1개월 전 납부 상태", "PAY_2": "2개월 전 납부 상태", "PAY_3": "3개월 전 납부 상태",
    "PAY_4": "4개월 전 납부 상태", "PAY_5": "5개월 전 납부 상태", "PAY_6": "6개월 전 납부 상태",
    "BILL_AMT1": "1개월 전 청구액", "BILL_AMT2": "2개월 전 청구액", "BILL_AMT3": "3개월 전 청구액",
    "BILL_AMT4": "4개월 전 청구액", "BILL_AMT5": "5개월 전 청구액", "BILL_AMT6": "6개월 전 청구액",
    "PAY_AMT1": "1개월 전 납부액", "PAY_AMT2": "2개월 전 납부액", "PAY_AMT3": "3개월 전 납부액",
    "PAY_AMT4": "4개월 전 납부액", "PAY_AMT5": "5개월 전 납부액", "PAY_AMT6": "6개월 전 납부액",
}


def load_model():
    for path in MODEL_CANDIDATES:
        if Path(path).exists():
            return joblib.load(path), path
    raise FileNotFoundError("모델 파일을 찾을 수 없습니다")


def validate_input(data: dict):
    errors = []
    if not (10000 <= data["LIMIT_BAL"] <= 1000000):
        errors.append("LIMIT_BAL이 유효 범위를 벗어났습니다")
    if not (18 <= data["AGE"] <= 100):
        errors.append("AGE가 유효 범위를 벗어났습니다")

    for col in [f"BILL_AMT{i}" for i in range(1, 7)] + [f"PAY_AMT{i}" for i in range(1, 7)]:
        if not (0 <= data[col] <= 10000000):
            errors.append(f"{col}이 유효 범위를 벗어났습니다")

    for col in ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]:
        if not (-1 <= data[col] <= 9):
            errors.append(f"{col}이 유효 범위를 벗어났습니다")
    return errors


def classify_risk(prob: float):
    if prob < 0.10:
        return "안전", "한도 증액 가능", "#31b463", "#e8f6ed", "#32bf67"
    if prob < 0.30:
        return "주의", "모니터링 필요", "#d6aa00", "#fff6db", "#dfb619"
    if prob < 0.60:
        return "경고", "한도 축소 검토", "#eb7a1d", "#fff1e7", "#f38c2f"
    return "위험", "한도 정지 · 추심 검토", "#e3534a", "#ffeceb", "#ec5b52"


def make_input_df(data: dict) -> pd.DataFrame:
    return pd.DataFrame([[data[c] for c in FEATURE_ORDER]], columns=FEATURE_ORDER)


def gauge_chart(prob: float, color: str):
    p = prob * 100
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=p,
        number={"suffix": "%", "font": {"size": 32, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#7b8796", "tickfont": {"size": 11}},
            "bar": {"color": color, "thickness": 0.13},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 20], "color": "#dfeee5"},
                {"range": [20, 40], "color": "#f0ecd8"},
                {"range": [40, 60], "color": "#f4ebde"},
                {"range": [60, 100], "color": "#f6e8e6"},
            ],
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=18, r=18, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "sans-serif"},
    )
    fig.add_annotation(text="연체 확률 (%)", x=0.5, y=0.98, showarrow=False, font={"size": 14, "color": "#55606f"})
    return fig


def risk_status_chart(current_label: str):
    labels = ["안전", "주의", "경고", "위험"]
    heights = [100 if l == current_label else 18 for l in labels]
    colors = ["#2fb160", "#d9b116", "#ea7f24", "#e5534a"]
    fig = go.Figure(go.Bar(
        x=labels,
        y=heights,
        marker_color=colors,
        text=["← 현재" if l == current_label else "" for l in labels],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(visible=False, range=[0, 120]),
        xaxis=dict(title=None, tickfont={"size": 15, "color": "#6c7786"}),
        showlegend=False,
    )
    return fig


def human_summary(data: dict):
    basic = pd.DataFrame([
        {"항목": "신용 한도", "값": f"{data['LIMIT_BAL']:,}원"},
        {"항목": "성별", "값": next(k for k, v in SEX_MAP.items() if v == data['SEX'])},
        {"항목": "학력", "값": next(k for k, v in EDU_MAP.items() if v == data['EDUCATION'])},
        {"항목": "혼인 상태", "값": next(k for k, v in MARRIAGE_MAP.items() if v == data['MARRIAGE'])},
        {"항목": "나이", "값": f"{data['AGE']}세"},
    ])
    pay_stat = pd.DataFrame([
        {"월": f"{i}개월 전", "상태": data[col]} for i, col in zip([1,2,3,4,5,6], ["PAY_0","PAY_2","PAY_3","PAY_4","PAY_5","PAY_6"])
    ])
    bill = pd.DataFrame([
        {"월": f"{i}개월 전", "청구액": f"{data[col]:,}원"} for i, col in zip([1,2,3,4,5,6], [f"BILL_AMT{i}" for i in range(1,7)])
    ])
    payment = pd.DataFrame([
        {"월": f"{i}개월 전", "납부액": f"{data[col]:,}원"} for i, col in zip([1,2,3,4,5,6], [f"PAY_AMT{i}" for i in range(1,7)])
    ])
    return basic, pay_stat, bill, payment


@st.cache_resource(show_spinner=False)
def cached_model():
    return load_model()


with st.sidebar:
    st.markdown("<div class='sidebar-group'>🧾 고객 기본 정보</div>", unsafe_allow_html=True)
    limit_bal = st.number_input("신용 한도", min_value=10000, max_value=1000000, value=30000, step=10000)
    sex = st.selectbox("성별", list(SEX_MAP.keys()), index=0)
    education = st.selectbox("학력", list(EDU_MAP.keys()), index=1)
    marriage = st.selectbox("혼인 상태", list(MARRIAGE_MAP.keys()), index=1)
    age = st.number_input("나이", min_value=18, max_value=100, value=35, step=1)

    st.markdown("<div class='sidebar-group'>💳 최근 6개월 결제 납부 상태</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-note'>-1은 정상, 1 이상은 연체 개월 수</div>", unsafe_allow_html=True)
    pay_0 = st.selectbox("1개월 전 상태", list(PAY_MAP.keys()), index=1)
    pay_2 = st.selectbox("2개월 전 상태", list(PAY_MAP.keys()), index=1)
    pay_3 = st.selectbox("3개월 전 상태", list(PAY_MAP.keys()), index=1)
    pay_4 = st.selectbox("4개월 전 상태", list(PAY_MAP.keys()), index=1)
    pay_5 = st.selectbox("5개월 전 상태", list(PAY_MAP.keys()), index=1)
    pay_6 = st.selectbox("6개월 전 상태", list(PAY_MAP.keys()), index=1)

    st.markdown("<div class='sidebar-group'>🧾 최근 6개월 실제 청구금액 (원)</div>", unsafe_allow_html=True)
    bill_amt1 = st.number_input("1개월 전 청구액", min_value=0, max_value=10000000, value=10000, step=1000)
    bill_amt2 = st.number_input("2개월 전 청구액", min_value=0, max_value=10000000, value=10000, step=1000)
    bill_amt3 = st.number_input("3개월 전 청구액", min_value=0, max_value=10000000, value=8000, step=1000)
    bill_amt4 = st.number_input("4개월 전 청구액", min_value=0, max_value=10000000, value=8000, step=1000)
    bill_amt5 = st.number_input("5개월 전 청구액", min_value=0, max_value=10000000, value=7000, step=1000)
    bill_amt6 = st.number_input("6개월 전 청구액", min_value=0, max_value=10000000, value=7000, step=1000)

    st.markdown("<div class='sidebar-group'>🪙 최근 6개월 실제 납부금액 (원)</div>", unsafe_allow_html=True)
    pay_amt1 = st.number_input("1개월 전 납부액", min_value=0, max_value=10000000, value=3000, step=1000)
    pay_amt2 = st.number_input("2개월 전 납부액", min_value=0, max_value=10000000, value=3000, step=1000)
    pay_amt3 = st.number_input("3개월 전 납부액", min_value=0, max_value=10000000, value=2000, step=1000)
    pay_amt4 = st.number_input("4개월 전 납부액", min_value=0, max_value=10000000, value=2000, step=1000)
    pay_amt5 = st.number_input("5개월 전 납부액", min_value=0, max_value=10000000, value=2000, step=1000)
    pay_amt6 = st.number_input("6개월 전 납부액", min_value=0, max_value=10000000, value=2000, step=1000)

    predict_clicked = st.button("🔎 연체확률 예측", use_container_width=True)

input_data = {
    "LIMIT_BAL": int(limit_bal),
    "SEX": SEX_MAP[sex],
    "EDUCATION": EDU_MAP[education],
    "MARRIAGE": MARRIAGE_MAP[marriage],
    "AGE": int(age),
    "PAY_0": PAY_MAP[pay_0],
    "PAY_2": PAY_MAP[pay_2],
    "PAY_3": PAY_MAP[pay_3],
    "PAY_4": PAY_MAP[pay_4],
    "PAY_5": PAY_MAP[pay_5],
    "PAY_6": PAY_MAP[pay_6],
    "BILL_AMT1": int(bill_amt1),
    "BILL_AMT2": int(bill_amt2),
    "BILL_AMT3": int(bill_amt3),
    "BILL_AMT4": int(bill_amt4),
    "BILL_AMT5": int(bill_amt5),
    "BILL_AMT6": int(bill_amt6),
    "PAY_AMT1": int(pay_amt1),
    "PAY_AMT2": int(pay_amt2),
    "PAY_AMT3": int(pay_amt3),
    "PAY_AMT4": int(pay_amt4),
    "PAY_AMT5": int(pay_amt5),
    "PAY_AMT6": int(pay_amt6),
}

st.markdown("<div class='title-wrap'><div class='app-title'>💳 신용카드 연체확률 예측 시스템</div></div>", unsafe_allow_html=True)
st.markdown(
    "<div class='app-subtitle'>IOSF 설계 기반 · Pipeline: StandardScaler → PCA(10) → RandomForest · 입력변수 23개</div>",
    unsafe_allow_html=True,
)
st.markdown("<div class='top-rule'></div>", unsafe_allow_html=True)

try:
    model, model_path = cached_model()
except FileNotFoundError:
    st.error("모델 파일을 찾을 수 없습니다")
    st.stop()
except Exception:
    st.error("서비스 오류가 발생했습니다")
    st.code(traceback.format_exc())
    st.stop()

errors = validate_input(input_data)

if "pred_result" not in st.session_state:
    st.session_state.pred_result = None

if predict_clicked:
    if errors:
        st.warning("입력값이 유효 범위를 벗어났습니다")
    else:
        try:
            start = time.perf_counter()
            prob = float(model.predict_proba(make_input_df(input_data))[0][1])
            elapsed = time.perf_counter() - start
            if not (0.0 <= prob <= 1.0):
                st.error("예측에 실패했습니다. 입력값을 확인해주세요")
            else:
                risk, action, color, card_bg, accent = classify_risk(prob)
                st.session_state.pred_result = {
                    "prob": prob,
                    "risk": risk,
                    "action": action,
                    "color": color,
                    "bg": card_bg,
                    "accent": accent,
                    "elapsed": elapsed,
                }
        except Exception:
            st.error("서비스 오류가 발생했습니다")
            st.code(traceback.format_exc())

res = st.session_state.pred_result
if res is None:
    res = {"prob": 0.01, "risk": "안전", "action": "한도 증액 가능", "color": "#31b463", "bg": "#e8f6ed", "accent": "#32bf67", "elapsed": 0.0}

col1, col2, col3 = st.columns([0.9, 1.4, 1.15], gap="large")
with col1:
    delta_text = "↑ 저위험 ▼" if res["risk"] == "안전" else "↑ 중위험 ▼" if res["risk"] == "주의" else "↑ 고위험 ▼" if res["risk"] == "경고" else "↑ 최고위험 ▼"
    st.markdown("<div class='plain-metric-label'>연체 확률</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='plain-metric-value'>{res['prob']*100:.1f}%</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='risk-pill'>{delta_text}</div>", unsafe_allow_html=True)
with col2:
    st.markdown(
        f"""
        <div class='risk-card' style='background:{res['bg']}; border-left-color:{res['accent']};'>
            <div class='risk-bubble'></div>
            <div class='risk-name' style='color:{res['color']};'>{res['risk']}</div>
            <div class='risk-caption'>위험 등급</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class='action-card' style='background:{res['bg']}; border-left-color:{res['accent']};'>
            <div class='action-label'>권장 조치</div>
            <div class='action-value' style='color:{res['color']};'>{res['action']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:1.3rem'></div>", unsafe_allow_html=True)
plot_l, plot_r = st.columns([1.05, 1], gap="large")
with plot_l:
    st.markdown("<div class='section-kicker'>📊 연체확률 게이지</div>", unsafe_allow_html=True)
    st.plotly_chart(gauge_chart(res["prob"], res["color"]), use_container_width=True, config={"displayModeBar": False})
with plot_r:
    st.markdown("<div class='section-kicker'>🏷️ 위험등급 현황</div>", unsafe_allow_html=True)
    st.plotly_chart(risk_status_chart(res["risk"]), use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        "<div class='chip-row'>"
        "<div class='chip'>안전: 0% 이상 10% 미만</div>"
        "<div class='chip'>주의: 10% 이상 30% 미만</div>"
        "<div class='chip'>경고: 30% 이상 60% 미만</div>"
        "<div class='chip'>위험: 60% 이상</div>"
        "</div>",
        unsafe_allow_html=True,
    )

st.divider()
st.markdown("<div class='input-title'>📋 입력 데이터 요약</div>", unsafe_allow_html=True)

basic_df, pay_df, bill_df, payment_df = human_summary(input_data)
tab1, tab2, tab3, tab4 = st.tabs(["👤 기본정보", "💳 납부상태", "🧾 청구금액", "🪙 납부금액"])
with tab1:
    st.dataframe(basic_df, use_container_width=True, hide_index=True)
with tab2:
    st.dataframe(pay_df, use_container_width=True, hide_index=True)
with tab3:
    st.dataframe(bill_df, use_container_width=True, hide_index=True)
with tab4:
    st.dataframe(payment_df, use_container_width=True, hide_index=True)

st.caption(f"모델 파일: {model_path} · 적용 범위: 단일 고객 실시간 예측 · 예측 응답시간: {res['elapsed']:.2f}초")
if errors:
    with st.expander("유효성 검사 상세"):
        for e in errors:
            st.write(f"- {e}")
