import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, date as dt_date

from src.model import predict_count  # 너가 만든 predict_count 그대로 사용


# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Bike Demand Forecast",
    page_icon="🚲",
    layout="wide",
)

# =========================
# CSS (Design)
# =========================
st.markdown("""
<style>
/* Layout padding (header 잘림 방지) */
.block-container { padding-top: 3.6rem; padding-bottom: 2rem; }

/* Hide streamlit default UI */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Background */
.stApp {
  background: radial-gradient(circle at 10% 10%, #f7fbff 0%, #f7f9fc 30%, #f9fafb 100%);
}

/* Header card */
.hero {
  background: linear-gradient(90deg, #0ea5e9 0%, #6366f1 55%, #a855f7 100%);
  padding: 18px 20px;
  border-radius: 18px;
  color: white;
  box-shadow: 0 10px 26px rgba(17,24,39,0.16);
  border: 1px solid rgba(255,255,255,0.2);
}
.hero-title {
  font-size: 30px;
  font-weight: 900;
  letter-spacing: -0.2px;
}
.hero-sub {
  margin-top: 4px;
  opacity: 0.92;
  font-size: 14px;
}
.pill {
  display:inline-block;
  margin-left: 10px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.22);
  font-weight: 800;
  font-size: 12px;
}

/* Cards */
.card {
  background: rgba(255,255,255,0.88);
  border: 1px solid #eef2f7;
  border-radius: 18px;
  padding: 14px 14px;
  box-shadow: 0 6px 16px rgba(0,0,0,0.06);
  transition: transform 0.14s ease, box-shadow 0.14s ease;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(0,0,0,0.10);
}
.muted { color:#6b7280; font-size:0.92rem; }
.big { color:#111827; font-weight:900; font-size:2rem; }
.midbig { color:#111827; font-weight:850; font-size:1.2rem; }

.badge { display:inline-block; padding:0.35rem 0.7rem; border-radius:999px; font-weight:900; font-size:0.85rem; }
.badge-low { background:#dcfce7; color:#166534; }
.badge-mid { background:#fef3c7; color:#92400e; }
.badge-high { background:#fee2e2; color:#991b1b; }

.section-title { font-size: 1.15rem; font-weight: 900; color:#111827; margin: 8px 0 10px; }
.hr { height:10px; }
.kpi-card {
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.kpi-card {
  min-height: 110px;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  padding: 14px 16px;
}
.kpi-top { display:flex; align-items:center; justify-content:space-between; }
.kpi-label { font-size: 0.86rem; color:#6b7280; font-weight: 700; }
.kpi-main { font-size: 1.8rem; font-weight: 900; color:#111827; line-height: 1.15; }
.kpi-sub { font-size: 0.9rem; color:#6b7280; margin-top: 6px; }
.kpi-chip {
  display:inline-flex; align-items:center; gap:6px;
  padding: 6px 10px; border-radius: 999px;
  background:#f3f4f6; color:#111827; font-weight: 800; font-size: 0.82rem;
}
.kpi-muted-chip {
  display:inline-flex; align-items:center; gap:6px;
  padding: 6px 10px; border-radius: 999px;
  background:#eef2ff; color:#3730a3; font-weight: 850; font-size: 0.82rem;
}
.kpi-row { display:flex; gap:10px; flex-wrap:wrap; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

# =========================
# Constants / Maps
# =========================
SEASON_MAP = {1: "봄", 2: "여름", 3: "가을", 4: "겨울"}

# 우리 내부 weather(1~4) 표기용
WEATHER_CAT = {
    1: ("☀️", "맑음"),
    2: ("⛅", "구름"),
    3: ("🌦️", "비/흐림"),
    4: ("🌧️", "악천후"),
}

def yesno_to_int(x: str) -> int:
    return 1 if x.strip().lower() in ["yes", "y", "true", "1"] else 0

def congestion_badge(pred: float):
    if pred < 150:
        return "여유", "badge-low"
    if pred < 300:
        return "보통", "badge-mid"
    return "혼잡", "badge-high"

def safe_parse_datetime(d: dt_date, hour: int):
    # date_input + hour -> datetime
    try:
        return datetime(d.year, d.month, d.day, int(hour), 0, 0)
    except Exception:
        return None

def map_openmeteo_code_to_cat(code: int) -> int:
    """
    Open-Meteo weather_code -> our 1~4 category
    (대충 '서비스용' 분류)
    """
    if code is None:
        return 2
    # clear
    if code == 0:
        return 1
    # mainly clear/partly cloudy
    if code in [1, 2, 3]:
        return 2
    # fog / drizzle / light rain
    if code in [45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67]:
        return 3
    # snow / heavy rain / thunder
    if code in [71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99]:
        return 4
    return 3

# =========================
# Open-Meteo helpers (no key)
# =========================
@st.cache_data(show_spinner=False, ttl=60 * 30)
def geocode_city(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if "results" not in data or not data["results"]:
        raise ValueError("도시를 찾을 수 없습니다.")
    item = data["results"][0]
    return float(item["latitude"]), float(item["longitude"]), item["name"]

@st.cache_data(show_spinner=False, ttl=60 * 30)
def fetch_weather_day(city: str, d: dt_date):
    """
    선택한 날짜 하루치(시간별) 날씨를 한번에 가져옴
    """
    lat, lon, resolved = geocode_city(city)
    url = "https://api.open-meteo.com/v1/forecast"
    date_str = d.strftime("%Y-%m-%d")
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
        "start_date": date_str,
        "end_date": date_str,
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if r.status_code != 200 or "hourly" not in data:
        reason = data.get("reason", "hourly 데이터가 없습니다.")
        raise ValueError(f"날씨 API 오류: {reason}")

    hourly = pd.DataFrame({
        "time": data["hourly"]["time"],
        "temp": data["hourly"]["temperature_2m"],
        "humidity": data["hourly"]["relative_humidity_2m"],
        "atemp": data["hourly"]["apparent_temperature"],
        "windspeed": data["hourly"]["wind_speed_10m"],
        "weather_code": data["hourly"]["weather_code"],
    })
    hourly["time"] = pd.to_datetime(hourly["time"])
    hourly["hour"] = hourly["time"].dt.hour
    hourly["weather_cat"] = hourly["weather_code"].apply(map_openmeteo_code_to_cat)
    return resolved, hourly


# =========================
# Session storage
# =========================
if "logs" not in st.session_state:
    st.session_state["logs"] = []  # in-memory logs (Cloud에서도 안정)

# =========================
# Header (Hero)
# =========================
st.markdown("""
<div class="hero">
  <div class="hero-title">🚲 Bike Demand Forecast</div>
  <div class="hero-sub">
    LightGBM 기반 실시간 자전거 수요 예측 대시보드
    <span class="pill">LIVE</span>
  </div>
</div>
<div class="hr"></div>
""", unsafe_allow_html=True)


# =========================
# Sidebar Inputs (User-friendly)
# =========================
with st.sidebar:
    st.header("입력")
    city = st.text_input("도시", value="Seoul")

    # 더 사용자 친화적인 입력: date + hour
    today = datetime.now().date()
    sel_date = st.date_input("날짜", value=today)

    sel_hour = st.select_slider("시간(시)", options=list(range(0, 24)), value=datetime.now().hour)

    season = st.selectbox("계절", [1, 2, 3, 4], format_func=lambda x: f"{SEASON_MAP[x]}", index=3)

    holiday_label = st.selectbox("Holiday", ["No", "Yes"], index=0)
    working_label = st.selectbox("Working Day", ["No", "Yes"], index=1)
    holiday = yesno_to_int(holiday_label)
    workingday = yesno_to_int(working_label)

    st.markdown("---")

    weather_mode = st.radio("날씨 입력 방식", ["Auto (Weather API)", "Manual"], index=0)

    # 기본 값 세팅
    if "temp" not in st.session_state:
        st.session_state["temp"] = 10.0
    if "atemp" not in st.session_state:
        st.session_state["atemp"] = 10.0
    if "humidity" not in st.session_state:
        st.session_state["humidity"] = 50.0
    if "windspeed" not in st.session_state:
        st.session_state["windspeed"] = 10.0
    if "weather_cat" not in st.session_state:
        st.session_state["weather_cat"] = 2

    if weather_mode.startswith("Auto"):
        if st.button("날씨 자동 불러오기", use_container_width=True):
            try:
                resolved, hourly = fetch_weather_day(city, sel_date)
                row = hourly[hourly["hour"] == int(sel_hour)]
                if row.empty:
                    raise ValueError("선택한 시간대 날씨 데이터를 찾지 못했습니다.")
                row = row.iloc[0]
                st.session_state["temp"] = float(row["temp"])
                st.session_state["atemp"] = float(row["atemp"])
                st.session_state["humidity"] = float(row["humidity"])
                st.session_state["windspeed"] = float(row["windspeed"])
                st.session_state["weather_cat"] = int(row["weather_cat"])
                st.success(f"{resolved} / {sel_date} {sel_hour:02d}:00 기준 반영 완료")
            except Exception as e:
                st.error(str(e))

        # 자동 모드에서도 값은 보여주되 수정 가능(미세 조정)
        temp = st.number_input("기온(°C)", value=float(st.session_state["temp"]))
        atemp = st.number_input("체감온도(°C)", value=float(st.session_state["atemp"]))
        humidity = st.number_input("습도(%)", value=float(st.session_state["humidity"]))
        windspeed = st.number_input("풍속(km/h)", value=float(st.session_state["windspeed"]))

        # category는 자동으로 잡히지만, 필요하면 수정도 가능하게
        weather = st.selectbox(
            "Weather Category",
            [1, 2, 3, 4],
            index=[1,2,3,4].index(int(st.session_state["weather_cat"])),
            format_func=lambda x: f"{WEATHER_CAT[x][0]} {WEATHER_CAT[x][1]}",
        )

    else:
        weather = st.selectbox(
            "Weather Category",
            [1, 2, 3, 4],
            format_func=lambda x: f"{WEATHER_CAT[x][0]} {WEATHER_CAT[x][1]}",
            index=1
        )
        temp = st.number_input("기온(°C)", value=float(st.session_state["temp"]))
        atemp = st.number_input("체감온도(°C)", value=float(st.session_state["atemp"]))
        humidity = st.number_input("습도(%)", value=float(st.session_state["humidity"]))
        windspeed = st.number_input("풍속(km/h)", value=float(st.session_state["windspeed"]))

    st.markdown("---")
    do_predict = st.button("예측하기", use_container_width=True, type="primary")


# =========================
# Build datetime string for model
# =========================
sel_dt = safe_parse_datetime(sel_date, sel_hour)
if sel_dt is None:
    st.error("날짜/시간 입력이 올바르지 않습니다.")
    st.stop()

dt_str = sel_dt.strftime("%Y-%m-%d %H:00:00")


# =========================
# Prediction
# =========================
pred = None
payload = None

if do_predict:
    payload = {
        "city": city,                  # 모델에는 안 쓰지만 기록용으로 남김
        "datetime": dt_str,
        "season": int(season),
        "holiday": int(holiday),
        "workingday": int(workingday),
        "weather": int(weather),
        "temp": float(temp),
        "atemp": float(atemp),
        "humidity": float(humidity),
        "windspeed": float(windspeed),
    }
    pred = predict_count(payload)

    st.session_state["logs"].append({
        "created_at": datetime.now(),
        "city": city,
        "input_datetime": dt_str,
        "season": SEASON_MAP[int(season)],
        "holiday": "Yes" if holiday == 1 else "No",
        "workingday": "Yes" if workingday == 1 else "No",
        "weather": WEATHER_CAT[int(weather)][1],
        "temp": float(temp),
        "humidity": float(humidity),
        "windspeed": float(windspeed),
        "predicted_count": float(pred),
    })
    st.session_state["logs"] = st.session_state["logs"][-300:]  # 최근 300개


# =========================
# KPI Cards
# =========================
emoji, wlabel = WEATHER_CAT[int(weather)]
work_txt = "Yes" if workingday == 1 else "No"
holiday_txt = "Yes" if holiday == 1 else "No"

# last delta
delta_txt = ""
if len(st.session_state["logs"]) >= 2:
    last = st.session_state["logs"][-1]["predicted_count"]
    prev = st.session_state["logs"][-2]["predicted_count"]
    diff = last - prev
    if abs(diff) >= 1:
        arrow = "▲" if diff > 0 else "▼"
        delta_txt = f"{arrow} {abs(diff):.0f}"

badge_text, badge_cls = congestion_badge(pred if pred is not None else 0)

c1, c2, c3, c4 = st.columns(4)
# KPI Cards (깔끔 버전)
pred_value = "-" if pred is None else f"{pred:,.0f} 대/시간"
work_txt = "Yes" if workingday == 1 else "No"
holiday_txt = "Yes" if holiday == 1 else "No"

emoji, wlabel = WEATHER_CAT[int(weather)]
badge_text, badge_cls = congestion_badge(pred if pred is not None else 0)

# 날씨 요약 한 줄 (가독성)
weather_summary = f"{temp:.1f}°C · 체감 {atemp:.1f}°C · 💧{humidity:.0f}% · 🌬{windspeed:.1f}"

st.markdown(f"""
<div class="kpi-grid">
  <div class="card kpi-card">
    <div class="kpi-top">
      <div class="kpi-label">예측 수요</div>
      <div class="kpi-muted-chip">Model · LGBM</div>
    </div>
    <div class="kpi-main">{pred_value}</div>
    <div class="kpi-sub">혼잡도 기준: 150 / 300</div>
  </div>

  <div class="card kpi-card">
    <div class="kpi-top">
      <div class="kpi-label">입력 정보</div>
      <div class="kpi-chip">📍 {city}</div>
    </div>
    <div class="kpi-main" style="font-size:1.1rem; font-weight:900;">
      {dt_str}
    </div>
    <div class="kpi-row">
      <span class="kpi-chip">🗓 {SEASON_MAP[int(season)]}</span>
      <span class="kpi-chip">Work: {work_txt}</span>
      <span class="kpi-chip">Holiday: {holiday_txt}</span>
    </div>
  </div>

  <div class="card kpi-card">
    <div class="kpi-top">
      <div class="kpi-label">날씨</div>
      <div class="kpi-chip">{emoji} {wlabel}</div>
    </div>
    <div class="kpi-main" style="font-size:1.1rem; font-weight:900;">
      {weather_summary}
    </div>
    <div class="kpi-sub">Auto Weather: {("On" if weather_mode.startswith("Auto") else "Off")}</div>
  </div>

  <div class="card kpi-card">
    <div class="kpi-top">
      <div class="kpi-label">혼잡도</div>
      <div class="badge {badge_cls}">{badge_text}</div>
    </div>
    <div class="kpi-main" style="font-size:1.15rem;">
      {("High demand expected" if badge_text=="혼잡" else ("Moderate demand" if badge_text=="보통" else "Low demand"))}
    </div>
    <div class="kpi-sub">운영 액션: {("추가 배치/재배치 고려" if badge_text=="혼잡" else ("모니터링" if badge_text=="보통" else "일반 운영"))}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# =========================
# Main Charts
# =========================
left, right = st.columns([1.25, 1])

with left:
    st.markdown("<div class='section-title'>예측 게이지</div>", unsafe_allow_html=True)
    if pred is None:
        st.info("왼쪽에서 입력 후 **예측하기**를 눌러주세요.")
    else:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=float(pred),
            number={"font": {"size": 36}},
            title={"text": "Predicted Demand"},
            gauge={
                "axis": {"range": [0, 500]},
                "bar": {"thickness": 0.28},
                "steps": [
                    {"range": [0, 150], "color": "#dcfce7"},
                    {"range": [150, 300], "color": "#fef3c7"},
                    {"range": [300, 500], "color": "#fee2e2"},
                ],
                "threshold": {"line": {"color": "#111827", "width": 4}, "value": float(pred)}
            }
        ))
        gauge.update_layout(height=320, margin=dict(l=18, r=18, t=45, b=20))
        st.plotly_chart(gauge, use_container_width=True)

with right:
    st.markdown("<div class='section-title'>오늘 24시간 예측 시뮬레이션</div>", unsafe_allow_html=True)

    # 24h prediction: 자동 날씨면 하루치 날씨를 가져와서 시간별 입력에 반영
    use_api_weather_for_day = weather_mode.startswith("Auto")

    hourly_weather = None
    resolved_city = city
    if use_api_weather_for_day:
        try:
            resolved_city, hourly_weather = fetch_weather_day(city, sel_date)
        except Exception:
            hourly_weather = None

    rows = []
    for h in range(24):
        dt_hour = datetime(sel_date.year, sel_date.month, sel_date.day, h, 0, 0)
        dt_hour_str = dt_hour.strftime("%Y-%m-%d %H:00:00")

        if hourly_weather is not None:
            wrow = hourly_weather[hourly_weather["hour"] == h]
            if not wrow.empty:
                wrow = wrow.iloc[0]
                t_temp = float(wrow["temp"])
                t_atemp = float(wrow["atemp"])
                t_hum = float(wrow["humidity"])
                t_wind = float(wrow["windspeed"])
                t_weather = int(wrow["weather_cat"])
            else:
                # fallback: 현재 입력값
                t_temp, t_atemp, t_hum, t_wind, t_weather = float(temp), float(atemp), float(humidity), float(windspeed), int(weather)
        else:
            # manual or failed fetch: 입력값 고정
            t_temp, t_atemp, t_hum, t_wind, t_weather = float(temp), float(atemp), float(humidity), float(windspeed), int(weather)

        p = {
            "city": resolved_city,
            "datetime": dt_hour_str,
            "season": int(season),
            "holiday": int(holiday),
            "workingday": int(workingday),
            "weather": int(t_weather),
            "temp": t_temp,
            "atemp": t_atemp,
            "humidity": t_hum,
            "windspeed": t_wind,
        }
        yhat = predict_count(p)
        rows.append({"hour": h, "predicted": yhat})

    day_df = pd.DataFrame(rows)

    fig_day = px.area(
        day_df,
        x="hour",
        y="predicted",
        markers=True,
        title=f"{resolved_city} · {sel_date} (0~23시)"
    )
    fig_day.update_layout(height=320, xaxis=dict(dtick=1), yaxis_title="Predicted Count")
    # 선택한 시간 강조
    fig_day.add_vline(x=int(sel_hour), line_width=3, line_dash="dash")
    st.plotly_chart(fig_day, use_container_width=True)

st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

# =========================
# Logs / Distribution
# =========================
st.markdown("<div class='section-title'>최근 예측 히스토리</div>", unsafe_allow_html=True)

if len(st.session_state["logs"]) == 0:
    st.info("아직 히스토리가 없어요. 예측을 한 번 실행해보자!")
else:
    log_df = pd.DataFrame(st.session_state["logs"])
    log_df["created_at"] = pd.to_datetime(log_df["created_at"])
    log_df = log_df.sort_values("created_at")

    colA, colB = st.columns([1.4, 1])
    with colA:
        fig_line = px.line(log_df, x="created_at", y="predicted_count", markers=True, title="예측값 추이")
        fig_line.update_layout(height=340)
        st.plotly_chart(fig_line, use_container_width=True)

    with colB:
        # ✅ 너가 원한 박스플롯
        fig_box = px.box(log_df, y="predicted_count", title="예측값 분포 (Box Plot)")
        fig_box.update_layout(height=340)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("<div class='section-title'>최근 로그 테이블</div>", unsafe_allow_html=True)
    st.dataframe(
        log_df.sort_values("created_at", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # CSV 다운로드
    csv = log_df.sort_values("created_at", ascending=False).to_csv(index=False).encode("utf-8-sig")
    st.download_button("로그 CSV 다운로드", data=csv, file_name="prediction_logs.csv", mime="text/csv")