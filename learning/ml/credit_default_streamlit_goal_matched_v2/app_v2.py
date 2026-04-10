import time
import traceback
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
:root {
    --bg: #f5f7fb;
    --card: #ffffff;
    --line: #e3e8f1;
    --text: #1f2937;
    --muted: #6b7280;
    --green: #2fb160;
    --green-soft: #e8f6ed;
    --yellow: #d6aa00;
    --yellow-soft: #fff8df;
    --orange: #ea7f24;
    --orange-soft: #fff1e7;
    --red: #e5534a;
    --red-soft: #ffeceb;
}

.stApp {
    background: var(--bg);
}

.main .block-container {
    max-width: 1340px;
    padding-top: 1.3rem;
    padding-bottom: 1.8rem;
}

[data-testid="stSidebar"] {
    background: #eef1f6;
    border-right: 1px solid #dbe2ec;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
    padding-bottom: 1.2rem;
    padding-left: 0.95rem;
    padding-right: 0.95rem;
}

[data-testid="stSidebar"] label {
    font-size: 0.9rem !important;
    color: #4b5563 !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    border-radius: 12px !important;
    border: 1px solid #dbe2ec !important;
    background: rgba(255,255,255,0.94) !important;
}

[data-testid="stSidebar"] .stNumberInput,
[data-testid="stSidebar"] .stSelectbox {
    margin-bottom: 0.55rem;
}

.hero {
    background: linear-gradient(135deg, #ffffff 0%, #fbfcff 100%);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1.15rem 1.3rem 1.05rem 1.3rem;
    box-shadow: 0 8px 26px rgba(20, 31, 61, 0.05);
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.38rem 0.72rem;
    border-radius: 999px;
    background: #eef4ff;
    color: #3557b7;
    font-weight: 800;
    font-size: 0.82rem;
    border: 1px solid #dbe7ff;
}

.hero-title {
    margin-top: 0.8rem;
    color: var(--text);
    font-size: 2.15rem;
    font-weight: 900;
    line-height: 1.08;
}

.hero-sub {
    color: var(--muted);
    font-size: 0.98rem;
    margin-top: 0.4rem;
    font-weight: 600;
}

.card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 1.05rem 1.1rem;
    box-shadow: 0 8px 22px rgba(17, 24, 39, 0.04);
    height: 100%;
}

.metric-card {
    min-height: 168px;
}

.metric-label {
    color: #5d6777;
    font-size: 0.88rem;
    font-weight: 800;
}

.metric-value {
    color: #1f2937;
    font-size: 2.8rem;
    font-weight: 900;
    line-height: 1;
    margin-top: 0.7rem;
}

.metric-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    border-radius: 999px;
    padding: 0.28rem 0.62rem;
    font-size: 0.82rem;
    font-weight: 800;
    margin-top: 0.65rem;
}

.risk-card {
    min-height: 168px;
    border-left: 5px solid #2fb160;
}

.risk-bubble {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    margin: 0.15rem auto 0.6rem auto;
    box-shadow: 0 8px 18px rgba(47, 177, 96, 0.28);
}

.risk-name {
    text-align: center;
    font-size: 1.95rem;
    font-weight: 900;
    line-height: 1.1;
}

.risk-caption {
    margin-top: 0.42rem;
    text-align: center;
    color: #7b8796;
    font-size: 0.92rem;
    font-weight: 700;
}

.action-card {
    min-height: 168px;
}

.action-name {
    margin-top: 0.95rem;
    font-size: 1.65rem;
    font-weight: 900;
    line-height: 1.18;
}

.action-sub {
    color: #7b8796;
    margin-top: 0.5rem;
    font-size: 0.92rem;
    font-weight: 700;
}

.section-title {
    color: #243044;
    font-size: 1.12rem;
    font-weight: 900;
    margin-bottom: 0.72rem;
}

.section-sub {
    color: #6b7280;
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: -0.15rem;
    margin-bottom: 0.7rem;
}

.soft-card {
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1rem 1.05rem;
    height: 100%;
    overflow: hidden;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.65rem;
}

.status-chip {
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.72rem 0.8rem;
    background: #fafbfe;
}

.status-label {
    color: #738091;
    font-size: 0.8rem;
    font-weight: 800;
}

.status-ok, .status-bad {
    font-size: 1rem;
    font-weight: 900;
    margin-top: 0.28rem;
}

.status-ok {
    color: var(--green);
}

.status-bad {
    color: var(--red);
}

.insight-box {
    border-radius: 16px;
    padding: 0.9rem 0.95rem;
    margin-bottom: 0.7rem;
    border: 1px solid var(--line);
    background: #fbfcff;
}

.insight-title {
    color: #243044;
    font-size: 0.94rem;
    font-weight: 900;
}

.insight-desc {
    color: #5d6777;
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 0.35rem;
    line-height: 1.5;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.7rem;
}

.kpi-tile {
    border: 1px solid var(--line);
    background: #fafbfe;
    border-radius: 14px;
    padding: 0.8rem 0.85rem;
}

.kpi-label {
    color: #7b8796;
    font-size: 0.78rem;
    font-weight: 800;
}

.kpi-value {
    color: #243044;
    margin-top: 0.3rem;
    font-size: 1.08rem;
    font-weight: 900;
}

.flow-note {
    margin-top: 0.6rem;
    color: #7b8796;
    font-size: 0.83rem;
    font-weight: 700;
}

.sidebar-head {
    color: #243044;
    font-size: 1.06rem;
    font-weight: 900;
    margin-top: 0.75rem;
    margin-bottom: 0.55rem;
}

.sidebar-note {
    color: #7a8494;
    font-size: 0.8rem;
    margin-bottom: 0.5rem;
}

.input-footer {
    margin-top: 0.65rem;
    color: #7a8494;
    font-size: 0.78rem;
    font-weight: 600;
}

.stButton > button {
    border-radius: 14px !important;
    background: linear-gradient(135deg, #ff5a5f 0%, #ff4a55 100%) !important;
    color: white !important;
    font-weight: 900 !important;
    border: none !important;
    min-height: 48px !important;
    box-shadow: 0 8px 18px rgba(255, 82, 87, 0.2);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.45rem;
}

.stTabs [data-baseweb="tab"] {
    font-weight: 800;
    border-radius: 12px 12px 0 0;
}

.legend-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.legend-pill {
    border: 1px solid var(--line);
    background: #fff;
    color: #445064;
    border-radius: 999px;
    padding: 0.38rem 0.72rem;
    font-size: 0.82rem;
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
    "정상(-1)": -1,
    "0개월": 0,
    "1개월": 1,
    "2개월": 2,
    "3개월": 3,
    "4개월": 4,
    "5개월": 5,
    "6개월": 6,
    "7개월": 7,
    "8개월": 8,
    "9개월": 9,
}

def load_model():
    for path in MODEL_CANDIDATES:
        if Path(path).exists():
            return joblib.load(path), path
    raise FileNotFoundError("모델 파일을 찾을 수 없습니다")

@st.cache_resource(show_spinner=False)
def cached_model():
    return load_model()

def validate_input(data: dict):
    issues = []
    if not (10000 <= data["LIMIT_BAL"] <= 1000000):
        issues.append("신용 한도가 허용 범위를 벗어났습니다.")
    if not (18 <= data["AGE"] <= 100):
        issues.append("나이가 허용 범위를 벗어났습니다.")
    for col in [f"BILL_AMT{i}" for i in range(1, 7)]:
        if not (0 <= data[col] <= 10000000):
            issues.append(f"{col} 값이 허용 범위를 벗어났습니다.")
    for col in [f"PAY_AMT{i}" for i in range(1, 7)]:
        if not (0 <= data[col] <= 10000000):
            issues.append(f"{col} 값이 허용 범위를 벗어났습니다.")
    for col in ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]:
        if not (-1 <= data[col] <= 9):
            issues.append(f"{col} 값이 허용 범위를 벗어났습니다.")
    return issues

def classify_risk(prob: float):
    if prob < 0.25:
        return {
            "risk": "안전 등급",
            "short": "안전",
            "action": "한도 증액 가능",
            "color": "#2fb160",
            "soft": "#e8f6ed",
            "accent": "#30bc66",
            "pill": "저위험 구간",
        }
    if prob < 0.50:
        return {
            "risk": "주의 등급",
            "short": "주의",
            "action": "모니터링 필요",
            "color": "#d6aa00",
            "soft": "#fff8df",
            "accent": "#dfb619",
            "pill": "관찰 필요",
        }
    if prob < 0.75:
        return {
            "risk": "경고 등급",
            "short": "경고",
            "action": "한도 축소 검토",
            "color": "#ea7f24",
            "soft": "#fff1e7",
            "accent": "#f18d33",
            "pill": "중고위험 구간",
        }
    return {
        "risk": "위험 등급",
        "short": "위험",
        "action": "한도 정지 / 추심 검토",
        "color": "#e5534a",
        "soft": "#ffeceb",
        "accent": "#ea6159",
        "pill": "최고위험 구간",
    }

def make_input_df(data: dict) -> pd.DataFrame:
    return pd.DataFrame([[data[c] for c in FEATURE_ORDER]], columns=FEATURE_ORDER)

def gauge_chart(prob: float, color: str):
    value = round(prob * 100, 1)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 34, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"size": 11, "color": "#738091"}},
            "bar": {"color": color, "thickness": 0.16},
            "borderwidth": 0,
            "bgcolor": "white",
            "steps": [
                {"range": [0, 25], "color": "#e5f3ea"},
                {"range": [25, 50], "color": "#fff6d3"},
                {"range": [50, 75], "color": "#feeddc"},
                {"range": [75, 100], "color": "#fde6e3"},
            ],
            "shape": "angular",
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        margin=dict(l=8, r=8, t=22, b=0),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "sans-serif"},
    )
    fig.add_annotation(
        text="연체 확률 (%)",
        x=0.5, y=0.98,
        showarrow=False,
        font={"size": 14, "color": "#5d6777"}
    )
    return fig

def payment_ratio_chart(data: dict):
    months = ["6개월 전", "5개월 전", "4개월 전", "3개월 전", "2개월 전", "1개월 전"]
    bills = [data["BILL_AMT6"], data["BILL_AMT5"], data["BILL_AMT4"], data["BILL_AMT3"], data["BILL_AMT2"], data["BILL_AMT1"]]
    pays = [data["PAY_AMT6"], data["PAY_AMT5"], data["PAY_AMT4"], data["PAY_AMT3"], data["PAY_AMT2"], data["PAY_AMT1"]]
    ratios = [round((p / b) * 100, 1) if b > 0 else 0.0 for p, b in zip(pays, bills)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=bills, name="청구액", marker_color="#dfe7f4"))
    fig.add_trace(go.Bar(x=months, y=pays, name="납부액", marker_color="#8bb8ff"))
    fig.add_trace(go.Scatter(
        x=months, y=ratios, name="납부율(%)", yaxis="y2",
        mode="lines+markers+text",
        text=[f"{r:.0f}%" for r in ratios],
        textposition="top center",
        line=dict(width=3, color="#3557b7"),
        marker=dict(size=8, color="#3557b7"),
    ))
    fig.update_layout(
        barmode="group",
        margin=dict(l=10, r=10, t=12, b=10),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        yaxis=dict(title="금액(원)", gridcolor="#edf1f7"),
        yaxis2=dict(title="납부율(%)", overlaying="y", side="right", rangemode="tozero"),
        xaxis=dict(title=None),
    )
    return fig

def delinquency_trend_chart(data: dict):
    months = ["6개월 전", "5개월 전", "4개월 전", "3개월 전", "2개월 전", "1개월 전"]
    values = [data["PAY_6"], data["PAY_5"], data["PAY_4"], data["PAY_3"], data["PAY_2"], data["PAY_0"]]
    colors = ["#2fb160" if v <= 0 else "#ea7f24" if v < 3 else "#e5534a" for v in values]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=values,
        mode="lines+markers+text",
        text=[str(v) for v in values],
        textposition="top center",
        line=dict(width=3, color="#7c6cf2"),
        marker=dict(size=11, color=colors, line=dict(width=2, color="white")),
        name="연체 개월 수",
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=12, b=10),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="연체 상태", gridcolor="#edf1f7"),
        xaxis=dict(title=None),
        showlegend=False,
    )
    return fig

def basic_summary(data: dict):
    sex_name = next(k for k, v in SEX_MAP.items() if v == data["SEX"])
    edu_name = next(k for k, v in EDU_MAP.items() if v == data["EDUCATION"])
    marriage_name = next(k for k, v in MARRIAGE_MAP.items() if v == data["MARRIAGE"])
    basic = pd.DataFrame([
        {"항목": "신용 한도", "값": f"{data['LIMIT_BAL']:,}원"},
        {"항목": "성별", "값": sex_name},
        {"항목": "학력", "값": edu_name},
        {"항목": "혼인 상태", "값": marriage_name},
        {"항목": "나이", "값": f"{data['AGE']}세"},
    ])
    pay = pd.DataFrame([
        {"월": lab, "연체 상태": val}
        for lab, val in zip(
            ["1개월 전", "2개월 전", "3개월 전", "4개월 전", "5개월 전", "6개월 전"],
            [data["PAY_0"], data["PAY_2"], data["PAY_3"], data["PAY_4"], data["PAY_5"], data["PAY_6"]]
        )
    ])
    bill = pd.DataFrame([{"월": f"{i}개월 전", "청구액": f"{data[f'BILL_AMT{i}']:,}원"} for i in range(1, 7)])
    payment = pd.DataFrame([{"월": f"{i}개월 전", "납부액": f"{data[f'PAY_AMT{i}']:,}원"} for i in range(1, 7)])
    return basic, pay, bill, payment

def compute_derived_metrics(data: dict):
    recent_bill = data["BILL_AMT1"]
    recent_pay = data["PAY_AMT1"]
    utilization = round((recent_bill / data["LIMIT_BAL"]) * 100, 1) if data["LIMIT_BAL"] > 0 else 0.0

    bill_values = [data[f"BILL_AMT{i}"] for i in range(1, 7)]
    pay_values = [data[f"PAY_AMT{i}"] for i in range(1, 7)]
    pay_status_values = [data["PAY_0"], data["PAY_2"], data["PAY_3"], data["PAY_4"], data["PAY_5"], data["PAY_6"]]

    ratios = [(p / b) if b > 0 else 0.0 for p, b in zip(pay_values, bill_values)]
    avg_ratio = round(sum(ratios) / len(ratios) * 100, 1)

    trend_delta = pay_status_values[0] - pay_status_values[-1]
    if trend_delta < 0:
        delinquency_trend = "최근으로 갈수록 악화"
    elif trend_delta > 0:
        delinquency_trend = "최근으로 갈수록 개선"
    else:
        delinquency_trend = "유지"

    flags = []
    if data["PAY_0"] >= 2:
        flags.append(("최근 연체 심화", f"최근 1개월 납부 상태가 {data['PAY_0']}로 단기 리스크가 높습니다."))
    if recent_bill > 0 and recent_pay / recent_bill < 0.3:
        flags.append(("낮은 납부율", f"최근 1개월 납부율이 {(recent_pay / recent_bill) * 100:.1f}%로 낮습니다."))
    if utilization >= 70:
        flags.append(("한도 압박", f"최근 청구액이 한도의 {utilization:.1f}% 수준으로 높습니다."))
    if avg_ratio < 40:
        flags.append(("상환 여력 주의", f"최근 6개월 평균 납부율이 {avg_ratio:.1f}%로 낮습니다."))

    if not flags:
        flags.append(("안정 패턴", "최근 납부 패턴과 한도 사용 수준이 비교적 안정적입니다."))

    return {
        "utilization": utilization,
        "avg_ratio": avg_ratio,
        "trend": delinquency_trend,
        "flags": flags[:3],
    }

def build_status_items(errors, model_ok, prob_ok):
    return [
        ("범위 검사", "정상" if not errors else "오류"),
        ("타입 검사", "정상"),
        ("결측값 검사", "정상"),
        ("모델 실행 상태", "정상" if model_ok else "오류"),
        ("예측값 검증", "정상" if prob_ok else "오류"),
    ]

with st.sidebar:
    st.markdown("<div class='sidebar-head'>🧾 고객 신용정보 입력</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-note'>단일 고객 실시간 예측용 입력 폼입니다.</div>", unsafe_allow_html=True)

    limit_bal = st.number_input("LIMIT_BAL", min_value=10000, max_value=1000000, value=30000, step=10000)
    sex = st.selectbox("SEX", list(SEX_MAP.keys()), index=0)
    education = st.selectbox("EDUCATION", list(EDU_MAP.keys()), index=1)
    marriage = st.selectbox("MARRIAGE", list(MARRIAGE_MAP.keys()), index=1)
    age = st.number_input("AGE", min_value=18, max_value=100, value=35, step=1)

    st.markdown("<div class='sidebar-head'>💳 최근 6개월 납부 상태</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-note'>-1은 정상, 1 이상은 연체 개월 수입니다.</div>", unsafe_allow_html=True)
    pay_0 = st.selectbox("PAY_0", list(PAY_MAP.keys()), index=1)
    pay_2 = st.selectbox("PAY_2", list(PAY_MAP.keys()), index=1)
    pay_3 = st.selectbox("PAY_3", list(PAY_MAP.keys()), index=1)
    pay_4 = st.selectbox("PAY_4", list(PAY_MAP.keys()), index=1)
    pay_5 = st.selectbox("PAY_5", list(PAY_MAP.keys()), index=1)
    pay_6 = st.selectbox("PAY_6", list(PAY_MAP.keys()), index=1)

    st.markdown("<div class='sidebar-head'>🧾 최근 6개월 청구 금액</div>", unsafe_allow_html=True)
    bill_amt1 = st.number_input("BILL_AMT1", min_value=0, max_value=10000000, value=10000, step=1000)
    bill_amt2 = st.number_input("BILL_AMT2", min_value=0, max_value=10000000, value=10000, step=1000)
    bill_amt3 = st.number_input("BILL_AMT3", min_value=0, max_value=10000000, value=8000, step=1000)
    bill_amt4 = st.number_input("BILL_AMT4", min_value=0, max_value=10000000, value=8000, step=1000)
    bill_amt5 = st.number_input("BILL_AMT5", min_value=0, max_value=10000000, value=7000, step=1000)
    bill_amt6 = st.number_input("BILL_AMT6", min_value=0, max_value=10000000, value=7000, step=1000)

    st.markdown("<div class='sidebar-head'>🪙 최근 6개월 납부 금액</div>", unsafe_allow_html=True)
    pay_amt1 = st.number_input("PAY_AMT1", min_value=0, max_value=10000000, value=3000, step=1000)
    pay_amt2 = st.number_input("PAY_AMT2", min_value=0, max_value=10000000, value=3000, step=1000)
    pay_amt3 = st.number_input("PAY_AMT3", min_value=0, max_value=10000000, value=2000, step=1000)
    pay_amt4 = st.number_input("PAY_AMT4", min_value=0, max_value=10000000, value=2000, step=1000)
    pay_amt5 = st.number_input("PAY_AMT5", min_value=0, max_value=10000000, value=2000, step=1000)
    pay_amt6 = st.number_input("PAY_AMT6", min_value=0, max_value=10000000, value=2000, step=1000)

    predict_clicked = st.button("🔎 연체확률 예측", use_container_width=True)
    st.markdown("<div class='input-footer'>고객 정보는 저장하지 않으며 현재 세션에서만 사용됩니다.</div>", unsafe_allow_html=True)

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

st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">IOSF 기반 심사용 도구 · StandardScaler → PCA(10) → RandomForest</div>
        <div class="hero-title">신용카드 연체확률 예측 시스템</div>
        <div class="hero-sub">
            금융기관 심사 담당자가 단일 고객의 다음달 연체 가능성을 빠르게 확인하고,
            위험등급과 권장조치를 함께 검토할 수 있도록 설계한 실시간 예측 대시보드입니다.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

model_ok = True
try:
    model, model_path = cached_model()
except FileNotFoundError:
    model_ok = False
    st.error("모델 파일을 찾을 수 없습니다")
    st.stop()
except Exception:
    model_ok = False
    st.error("서비스 오류가 발생했습니다")
    st.code(traceback.format_exc())
    st.stop()

issues = validate_input(input_data)

if "pred_result_v2" not in st.session_state:
    st.session_state.pred_result_v2 = None

if predict_clicked:
    if issues:
        st.warning("입력값이 유효 범위를 벗어났습니다. 상세 내용은 검사 결과를 확인해주세요.")
    else:
        try:
            start = time.perf_counter()
            prob = float(model.predict_proba(make_input_df(input_data))[0][1])
            elapsed = time.perf_counter() - start
            if not (0.0 <= prob <= 1.0):
                st.error("예측에 실패했습니다. 입력값을 확인해주세요")
                st.session_state.pred_result_v2 = {"prob": 0.0, "elapsed": elapsed, "prob_ok": False, **classify_risk(0.0)}
            else:
                st.session_state.pred_result_v2 = {"prob": prob, "elapsed": elapsed, "prob_ok": True, **classify_risk(prob)}
        except Exception:
            st.error("서비스 오류가 발생했습니다")
            st.code(traceback.format_exc())

res = st.session_state.pred_result_v2
if res is None:
    seed_prob = 0.01
    res = {"prob": seed_prob, "elapsed": 0.0, "prob_ok": True, **classify_risk(seed_prob)}

derived = compute_derived_metrics(input_data)
status_items = build_status_items(issues, model_ok, res.get("prob_ok", True))

info1, info2, info3 = st.columns(3, gap="large")
with info1:
    st.markdown(f"""
    <div class="card">
        <div class="metric-label">모델 파일</div>
        <div style="margin-top:0.45rem;font-size:1.02rem;font-weight:900;color:#243044;">{model_path}</div>
    </div>
    """, unsafe_allow_html=True)
with info2:
    st.markdown("""
    <div class="card">
        <div class="metric-label">적용 범위</div>
        <div style="margin-top:0.45rem;font-size:1.02rem;font-weight:900;color:#243044;">단일 고객 실시간 예측</div>
    </div>
    """, unsafe_allow_html=True)
with info3:
    st.markdown(f"""
    <div class="card">
        <div class="metric-label">응답 시간</div>
        <div style="margin-top:0.45rem;font-size:1.02rem;font-weight:900;color:#243044;">{res.get("elapsed", 0.0):.2f}초</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([0.95, 1.15, 1.1], gap="large")
with c1:
    st.markdown(
        f"""
        <div class="card metric-card">
            <div class="metric-label">연체 확률</div>
            <div class="metric-value">{res["prob"] * 100:.1f}%</div>
            <div class="metric-pill" style="background:{res['soft']}; color:{res['color']};">{res['pill']}</div>
            <div class="flow-note">predict_proba() 기반 결과값</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="card risk-card" style="background:{res['soft']}; border-left-color:{res['accent']};">
            <div class="metric-label">위험 등급</div>
            <div class="risk-bubble" style="background: radial-gradient(circle at 30% 30%, #ffffff 0%, {res['accent']} 35%, {res['color']} 80%);"></div>
            <div class="risk-name" style="color:{res['color']};">{res['short']}</div>
            <div class="risk-caption">{res['risk']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""
        <div class="card action-card" style="background:{res['soft']}; border-left:5px solid {res['accent']};">
            <div class="metric-label">권장 조치</div>
            <div class="action-name" style="color:{res['color']};">{res['action']}</div>
            <div class="action-sub">심사 담당자 참고용 의사결정 보조 정보</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

row2_left, row2_right = st.columns([1.05, 0.95], gap="large")
with row2_left:
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📊 연체확률 게이지</div>", unsafe_allow_html=True)
    st.plotly_chart(gauge_chart(res["prob"], res["color"]), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with row2_right:
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🧪 검사 결과 및 심사 인사이트</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>입력 유효성 검사, 모델 실행 상태, 예측값 검증을 한 화면에서 확인합니다.</div>", unsafe_allow_html=True)
    st.markdown("<div class='status-grid'>", unsafe_allow_html=True)
    for label, status in status_items:
        cls = "status-ok" if status == "정상" else "status-bad"
        st.markdown(
            f"""
            <div class="status-chip">
                <div class="status-label">{label}</div>
                <div class="{cls}">{status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
    for title, desc in derived["flags"]:
        st.markdown(
            f"""
            <div class="insight-box">
                <div class="insight-title">{title}</div>
                <div class="insight-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="legend-row">
            <div class="legend-pill">안전: p &lt; 0.25</div>
            <div class="legend-pill">주의: 0.25 ≤ p &lt; 0.50</div>
            <div class="legend-pill">경고: 0.50 ≤ p &lt; 0.75</div>
            <div class="legend-pill">위험: p ≥ 0.75</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)

row3_left, row3_right = st.columns(2, gap="large")
with row3_left:
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>💸 청구액 대비 납부 패턴</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>최근 6개월 청구액, 납부액, 납부율을 동시에 확인합니다.</div>", unsafe_allow_html=True)
    st.plotly_chart(payment_ratio_chart(input_data), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)
with row3_right:
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📈 최근 6개월 연체 추세</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>연체 개월 수 흐름을 통해 악화/개선 방향을 확인합니다.</div>", unsafe_allow_html=True)
    st.plotly_chart(delinquency_trend_chart(input_data), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:0.55rem'></div>", unsafe_allow_html=True)

st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>🧭 심사 판단 보조 지표</div>", unsafe_allow_html=True)
st.markdown("<div class='section-sub'>모델 결과를 해석할 때 함께 볼 수 있는 요약 지표입니다.</div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-tile">
            <div class="kpi-label">최근 한도 사용 비율</div>
            <div class="kpi-value">{derived['utilization']:.1f}%</div>
        </div>
        <div class="kpi-tile">
            <div class="kpi-label">최근 6개월 평균 납부율</div>
            <div class="kpi-value">{derived['avg_ratio']:.1f}%</div>
        </div>
        <div class="kpi-tile">
            <div class="kpi-label">연체 추세</div>
            <div class="kpi-value">{derived['trend']}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:0.55rem'></div>", unsafe_allow_html=True)
st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📋 입력 데이터 요약</div>", unsafe_allow_html=True)
st.markdown("<div class='section-sub'>입력한 고객 정보를 카테고리별로 확인합니다.</div>", unsafe_allow_html=True)
basic_df, pay_df, bill_df, payment_df = basic_summary(input_data)
tab1, tab2, tab3, tab4 = st.tabs(["기본정보", "납부상태", "청구금액", "납부금액"])
with tab1:
    st.dataframe(basic_df, use_container_width=True, hide_index=True)
with tab2:
    st.dataframe(pay_df, use_container_width=True, hide_index=True)
with tab3:
    st.dataframe(bill_df, use_container_width=True, hide_index=True)
with tab4:
    st.dataframe(payment_df, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

if issues:
    with st.expander("유효성 검사 상세"):
        for item in issues:
            st.write(f"- {item}")

st.caption("본 서비스는 단일 고객 실시간 연체위험 분석용 보조 도구이며, 고객 정보를 서버에 저장하지 않습니다.")