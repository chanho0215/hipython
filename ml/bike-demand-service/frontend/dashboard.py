import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Bike Demand Forecast",
    page_icon="🚲",
    layout="wide"
)

# -----------------------------
# 스타일
# -----------------------------
st.markdown("""
<style>
.main {
    background-color: #f7f9fc;
}
.block-container {
    padding-top: 4rem;
    padding-bottom: 2rem;
}
.card {
    background: white;
    padding: 1.2rem 1.2rem;
    border-radius: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    border: 1px solid #eef2f7;
}
.card-title {
    font-size: 0.95rem;
    color: #6b7280;
    margin-bottom: 0.4rem;
}
.card-value {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
}
.badge {
    display: inline-block;
    padding: 0.35rem 0.7rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
}
.badge-low {
    background-color: #dcfce7;
    color: #166534;
}
.badge-mid {
    background-color: #fef3c7;
    color: #92400e;
}
.badge-high {
    background-color: #fee2e2;
    color: #991b1b;
}
.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin-top: 1rem;
    margin-bottom: 0.6rem;
    color: #111827;
}
.small-text {
    color: #6b7280;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 유틸 함수
# -----------------------------
WEATHER_MAP = {
    1: {"label": "맑음", "emoji": "☀️"},
    2: {"label": "구름 조금", "emoji": "⛅"},
    3: {"label": "약한 비/흐림", "emoji": "🌦️"},
    4: {"label": "강한 비/악천후", "emoji": "🌧️"},
}

SEASON_MAP = {
    1: "봄",
    2: "여름",
    3: "가을",
    4: "겨울"
}

def get_congestion_level(pred):
    if pred < 150:
        return "여유", "badge-low"
    elif pred < 300:
        return "보통", "badge-mid"
    else:
        return "혼잡", "badge-high"

def safe_get_weather(city):
    try:
        res = requests.get(f"{API_URL}/weather", params={"city": city}, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None

def safe_predict(payload):
    try:
        res = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
        if res.status_code == 200:
            return res.json()
        return {"error": f"{res.status_code} / {res.text}"}
    except Exception as e:
        return {"error": str(e)}

def safe_get_logs(limit=50):
    try:
        res = requests.get(f"{API_URL}/logs", params={"limit": limit}, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None

# -----------------------------
# 헤더
# -----------------------------
st.markdown("<div class='section-title'>🚲 Bike Demand Forecast Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='small-text'>LightGBM 기반 실시간 자전거 수요 예측 서비스</div>", unsafe_allow_html=True)

# -----------------------------
# 사이드바 입력
# -----------------------------
with st.sidebar:
    st.header("입력 파라미터")

    city = st.text_input("도시", value="Seoul")
    dt = st.text_input(
    "날짜/시간",
    value=datetime.now().strftime("%Y-%m-%d %H:00:00")
)

    season = st.selectbox(
        "계절",
        options=[1, 2, 3, 4],
        format_func=lambda x: f"{x} - {SEASON_MAP[x]}",
        index=3
    )

    holiday = st.selectbox(
        "휴일 여부",
        options=[0, 1],
        format_func=lambda x: "휴일" if x == 1 else "비휴일",
        index=0
    )

    workingday = st.selectbox(
        "근무일 여부",
        options=[0, 1],
        format_func=lambda x: "근무일" if x == 1 else "비근무일",
        index=1
    )

    weather = st.selectbox(
        "날씨 상태",
        options=[1, 2, 3, 4],
        format_func=lambda x: f"{WEATHER_MAP[x]['emoji']} {WEATHER_MAP[x]['label']}",
        index=0
    )

    st.markdown("---")

    if st.button("날씨 자동 불러오기", use_container_width=True):
      dt_parsed = pd.to_datetime(dt)
      selected_date = dt_parsed.strftime("%Y-%m-%d")
      selected_hour = int(dt_parsed.hour)

      res = requests.get(
        f"{API_URL}/weather",
        params={
            "city": city,
            "date": selected_date,
            "hour": selected_hour
        }
    )

      if res.status_code == 200:
        weather_data = res.json()
        st.session_state["temp"] = weather_data["temp"]
        st.session_state["atemp"] = weather_data["atemp"]
        st.session_state["humidity"] = weather_data["humidity"]
        st.session_state["windspeed"] = weather_data["windspeed"]
        st.success(f"{selected_date} {selected_hour}:00 기준 날씨를 불러왔어요.")
      else:
        st.error(f"날씨 조회 실패: {res.text}")

    temp = st.number_input("기온", value=float(st.session_state.get("temp", 10.0)))
    atemp = st.number_input("체감온도", value=float(st.session_state.get("atemp", 10.0)))
    humidity = st.number_input("습도", value=float(st.session_state.get("humidity", 50.0)))
    windspeed = st.number_input("풍속", value=float(st.session_state.get("windspeed", 10.0)))

    predict_clicked = st.button("예측하기", use_container_width=True, type="primary")

# -----------------------------
# 예측 실행
# -----------------------------
if "predicted_count" not in st.session_state:
    st.session_state["predicted_count"] = None

if predict_clicked:
    payload = {
        "city": city,
        "datetime": dt,
        "season": season,
        "holiday": holiday,
        "workingday": workingday,
        "weather": weather,
        "temp": temp,
        "atemp": atemp,
        "humidity": humidity,
        "windspeed": windspeed
    }

    result = safe_predict(payload)

    if "error" in result:
        st.error(f"예측 실패: {result['error']}")
    else:
        st.session_state["predicted_count"] = result["predicted_count"]
        st.session_state["last_payload"] = payload

# -----------------------------
# 상단 KPI 카드
# -----------------------------
pred = st.session_state.get("predicted_count")
weather_info = WEATHER_MAP[weather]
level_text, badge_class = get_congestion_level(pred if pred is not None else 0)

col1, col2, col3, col4 = st.columns(4)

with col1:
    value = f"{pred:.2f}" if pred is not None else "-"
    st.markdown(f"""
    <div class="card">
        <div class="card-title">예측 수요</div>
        <div class="card-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">입력 도시</div>
        <div class="card-value">{city}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">날씨 상태</div>
        <div class="card-value">{weather_info['emoji']} {weather_info['label']}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    badge_html = f"<span class='badge {badge_class}'>{level_text}</span>"
    st.markdown(f"""
    <div class="card">
        <div class="card-title">혼잡도</div>
        <div class="card-value">{badge_html}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# -----------------------------
# 메인 차트 영역
# -----------------------------
left, right = st.columns([1.2, 1])

with left:
    st.markdown("<div class='section-title'>예측 결과 시각화</div>", unsafe_allow_html=True)

    if pred is not None:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pred,
            number={"font": {"size": 36}},
            title={"text": "예측 수요"},
            gauge={
                "axis": {"range": [0, 500]},
                "bar": {"thickness": 0.3},
                "steps": [
                    {"range": [0, 150], "color": "#dcfce7"},
                    {"range": [150, 300], "color": "#fef3c7"},
                    {"range": [300, 500], "color": "#fee2e2"}
                ],
                "threshold": {
                    "line": {"color": "#111827", "width": 4},
                    "thickness": 0.8,
                    "value": pred
                }
            }
        ))
        gauge.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(gauge, use_container_width=True)
    else:
        st.info("왼쪽 사이드바에서 값을 입력하고 예측하기를 눌러주세요.")

with right:
    st.markdown("<div class='section-title'>현재 입력 요약</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div class="small-text">📅 날짜/시간</div>
        <div style="font-size:1.1rem; font-weight:600;">{dt}</div>
        <hr>
        <div class="small-text">🌡 기온 / 체감온도</div>
        <div style="font-size:1.1rem; font-weight:600;">{temp} / {atemp}</div>
        <hr>
        <div class="small-text">💧 습도 / 🌬 풍속</div>
        <div style="font-size:1.1rem; font-weight:600;">{humidity} / {windspeed}</div>
        <hr>
        <div class="small-text">🗂 계절 / 근무일 / 휴일</div>
        <div style="font-size:1.1rem; font-weight:600;">{SEASON_MAP[season]} / {workingday} / {holiday}</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# 최근 로그
# -----------------------------
st.markdown("")
st.markdown("<div class='section-title'>최근 예측 히스토리</div>", unsafe_allow_html=True)

logs = safe_get_logs(limit=50)

if logs is None:
    st.error("로그 조회 실패: /logs 엔드포인트를 확인해줘.")
elif len(logs) == 0:
    st.info("아직 저장된 로그가 없어요. 예측을 먼저 실행해보자.")
else:
    log_df = pd.DataFrame(logs)
    log_df["created_at"] = pd.to_datetime(log_df["created_at"])
    log_df = log_df.sort_values("created_at")

    c1, c2 = st.columns([1.3, 1])

    with c1:
        fig_line = px.line(
            log_df,
            x="created_at",
            y="predicted_count",
            markers=True,
            title="예측값 추이"
        )
        fig_line.update_layout(height=350)
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        fig_box = px.box(
            log_df,
            y="predicted_count",
            title="예측값 분포"
        )
        fig_box.update_layout(height=350)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("<div class='section-title'>최근 로그 테이블</div>", unsafe_allow_html=True)
    display_cols = [
        "created_at", "city", "input_datetime", "temp",
        "humidity", "windspeed", "predicted_count"
    ]
    st.dataframe(log_df[display_cols].sort_values("created_at", ascending=False), use_container_width=True)