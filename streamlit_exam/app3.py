# app.py
# 실행: streamlit run app.py

import time
from datetime import datetime, timedelta

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


# =============================================================================
# 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="크리에이터 스튜디오 Pro · 핑크 라이트",
    page_icon="💗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# CSS (밝은 핑크 테마)
# =============================================================================
def 스타일_적용() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

          :root{
            --bg: #fff7fb;
            --panel: rgba(255,255,255,0.78);
            --panel2: rgba(255,255,255,0.88);
            --bd: rgba(255, 77, 166, 0.18);
            --bd2: rgba(255, 77, 166, 0.28);
            --txt: rgba(22, 14, 26, 0.92);
            --muted: rgba(22, 14, 26, 0.62);
            --accent: #ff4da6;
            --accent2: #ff2f98;
            --accent3: #ffd1e8;

            --r-xl: 24px;
            --r-lg: 18px;
            --r-md: 14px;

            --shadowA: 0 18px 60px rgba(255, 77, 166, 0.12);
            --shadowB: 0 10px 28px rgba(30, 10, 30, 0.08);
          }

          html, body, [class*="css"]{
            font-family: 'Inter', sans-serif;
            color: var(--txt);
          }

          .stApp{
            background:
              radial-gradient(1200px 700px at 12% 0%, rgba(255, 77, 166, 0.14), rgba(255,255,255,0)),
              radial-gradient(900px 600px at 92% 10%, rgba(255, 123, 197, 0.16), rgba(255,255,255,0)),
              linear-gradient(180deg, #fff7fb 0%, #ffffff 55%, #fff7fb 100%);
          }

          .block-container{ padding-top: 1.0rem; }

          /* 사이드바 */
          [data-testid="stSidebar"]{
            border-right: 1px solid rgba(255, 77, 166, 0.14);
            background:
              radial-gradient(900px 360px at 30% 0%,
                rgba(255, 77, 166, 0.10), rgba(255,255,255,0)),
              linear-gradient(180deg, rgba(255,255,255,0.92), rgba(255,255,255,0.70));
          }

          /* 상단 메뉴 숨김(깔끔) */
          #MainMenu { visibility: hidden; }
          header { visibility: hidden; }
          footer { visibility: hidden; }

          /* 상단 바 */
          .topbar{
            border-radius: var(--r-xl);
            padding: 16px 18px;
            border: 1px solid var(--bd);
            background:
              radial-gradient(1000px 260px at 0% 0%, rgba(255, 77, 166, 0.18), rgba(255,255,255,0.60)),
              radial-gradient(900px 260px at 100% 15%, rgba(255, 123, 197, 0.20), rgba(255,255,255,0.70)),
              linear-gradient(180deg, rgba(255,255,255,0.86), rgba(255,255,255,0.66));
            box-shadow: var(--shadowA), var(--shadowB);
            backdrop-filter: blur(12px);
          }

          .badge{
            display:inline-flex; align-items:center; gap:8px;
            padding:6px 10px;
            border-radius:999px;
            border: 1px solid rgba(255, 77, 166, 0.24);
            background: rgba(255,255,255,0.78);
            color: var(--txt);
            font-size: 0.92rem;
            font-weight: 800;
            backdrop-filter: blur(10px);
          }
          .badge .dot{
            width:8px; height:8px; border-radius:999px;
            background: var(--accent);
            box-shadow: 0 0 18px rgba(255, 77, 166, 0.35);
          }

          .kicker{
            margin-top: 6px;
            font-size: 0.92rem;
            color: var(--muted);
          }

          .section-title{
            font-weight: 850;
            letter-spacing: -0.3px;
            margin: 0 0 8px 0;
            color: var(--txt);
          }

          /* 카드화 */
          div[data-testid="stMetric"],
          div[data-testid="stExpander"],
          div.stDataFrame,
          div[data-testid="stDataEditor"]{
            background-color: var(--panel);
            border: 1px solid var(--bd);
            padding: 14px 14px;
            border-radius: var(--r-lg);
            backdrop-filter: blur(12px);
            box-shadow: 0 10px 28px rgba(255, 77, 166, 0.08), 0 10px 24px rgba(30, 10, 30, 0.06);
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
          }

          div[data-testid="stMetric"]:hover{
            border-color: rgba(255, 77, 166, 0.42);
            transform: translateY(-2px);
            box-shadow: 0 14px 36px rgba(255, 77, 166, 0.12), 0 12px 28px rgba(30, 10, 30, 0.08);
          }

          /* 탭 */
          .stTabs [data-baseweb="tab-list"]{
            gap: 8px;
            background-color: rgba(255, 77, 166, 0.07);
            padding: 6px;
            border-radius: 14px;
            border: 1px solid rgba(255, 77, 166, 0.16);
          }
          .stTabs [data-baseweb="tab"]{
            height: 42px;
            border-radius: 10px;
            color: rgba(22, 14, 26, 0.62);
            font-weight: 800;
          }
          .stTabs [aria-selected="true"]{
            background-color: var(--accent) !important;
            color: white !important;
            box-shadow: 0 10px 22px rgba(255, 77, 166, 0.18);
          }

          /* 버튼 */
          .stButton > button{
            border-radius: 14px !important;
            border: 1px solid rgba(255, 77, 166, 0.20) !important;
            background: rgba(255,255,255,0.88) !important;
            white-space: nowrap !important;
          }
          .stButton > button:hover{
            border-color: rgba(255, 77, 166, 0.40) !important;
            background: rgba(255, 209, 232, 0.30) !important;
          }
          button[kind="primary"]{
            background: linear-gradient(180deg, var(--accent), var(--accent2)) !important;
            border: none !important;
            color: white !important;
            box-shadow: 0 14px 26px rgba(255, 77, 166, 0.18) !important;
          }

          /* 입력 */
          input, textarea{ border-radius: 12px !important; }

          /* 알테어 컨테이너 */
          .vega-embed{
            border-radius: var(--r-md) !important;
            overflow: hidden !important;
            border: 1px solid rgba(255, 77, 166, 0.16);
            background: var(--panel2);
          }

          /* 업로더 컴팩트 */
          [data-testid="stFileUploader"] section{ padding: 8px 10px !important; }
          [data-testid="stFileUploader"] small{ color: rgba(22, 14, 26, 0.58) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Altair 테마
# =============================================================================
def 알테어_테마_등록() -> None:
    def _theme():
        return {
            "config": {
                "background": "transparent",
                "view": {"stroke": "rgba(255,77,166,0.10)", "cornerRadius": 12},
                "axis": {
                    "labelColor": "rgba(22,14,26,0.68)",
                    "titleColor": "rgba(22,14,26,0.78)",
                    "gridColor": "rgba(255,77,166,0.10)",
                    "domainColor": "rgba(255,77,166,0.14)",
                    "tickColor": "rgba(255,77,166,0.14)",
                    "labelFont": "Inter",
                    "titleFont": "Inter",
                },
                "legend": {
                    "labelColor": "rgba(22,14,26,0.72)",
                    "titleColor": "rgba(22,14,26,0.78)",
                    "labelFont": "Inter",
                    "titleFont": "Inter",
                },
                "title": {"color": "rgba(22,14,26,0.86)", "font": "Inter", "fontSize": 14},
            }
        }

    alt.themes.register("pink_light_ko", _theme)
    alt.themes.enable("pink_light_ko")


# =============================================================================
# 데이터 생성
# =============================================================================
@st.cache_data(show_spinner=False)
def 채널_데이터_생성(days: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(int(seed))
    days = int(days)
    date_range = pd.date_range(end=datetime.today(), periods=days)

    base = np.linspace(6500, 17500, days)
    weekly = 1300 * np.sin(np.linspace(0, 3 * np.pi, days))
    spikes = rng.choice([1.0, 1.35, 2.4], size=days, p=[0.90, 0.08, 0.02])
    noise = rng.normal(0, 700, days)

    views = np.clip((base + weekly) * spikes + noise, 450, None).round().astype(int)
    subs = np.clip((views * rng.uniform(0.0012, 0.0048, days) + rng.normal(0, 6, days)), 0, None).round().astype(int)
    rpm = rng.uniform(2.2, 4.4, days)
    revenue = np.clip((views / 1000) * rpm + rng.normal(0, 6, days), 0, None)
    avg_dur = rng.uniform(220, 620, days)  # seconds
    ctr = np.clip(rng.normal(6.4, 1.4, days), 1.0, 16.0)

    df = pd.DataFrame(
        {
            "date": date_range,
            "views": views,
            "subs_gained": subs,
            "revenue": revenue,
            "avg_duration": avg_dur,
            "ctr": ctr,
        }
    )
    df["dow"] = df["date"].dt.day_name()
    df["is_spike"] = df["views"] > np.percentile(df["views"], 95)
    df["rpm"] = (df["revenue"] / (df["views"] / 1000)).replace([np.inf, -np.inf], np.nan).fillna(0)
    return df


@st.cache_data(show_spinner=False)
def 영상_목록_생성(count: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(int(seed))
    count = int(count)

    titles = [
        "VLOG: 서울의 하루 🇰🇷",
        "나의 데스크 셋업 2026",
        "AI 앱 10분 만에 만들기",
        "퇴사를 결심한 이유",
        "Streamlit 실전 UI 튜토리얼",
        "키보드 ASMR",
        "생산성 도구 TOP 5",
        "구독자 10만 Q&A",
        "여행 준비물 정리",
        "미니멀 룸 투어",
        "편집 워크플로우 (빠르게)",
        "콘텐츠 캘린더 운영법",
    ]

    data = []
    for i in range(count):
        step = int(rng.integers(2, 5))
        gap_days = int(i * step)  # FIX: timedelta에 numpy int 금지
        published = datetime.today() - timedelta(days=gap_days)

        views = int(rng.integers(8_000, 520_000))
        ctr = float(np.round(rng.uniform(2.6, 12.5), 1))
        revenue = float(np.round(rng.uniform(35, 2400), 2))
        duration = int(rng.integers(6, 22))

        data.append(
            {
                "영상 제목": titles[i % len(titles)],
                "게시일": published.strftime("%Y-%m-%d"),
                "길이(분)": duration,
                "조회수": views,
                "CTR(%)": ctr,
                "수익($)": revenue,
            }
        )

    return pd.DataFrame(data)


# =============================================================================
# 유틸
# =============================================================================
def 이전_행(df: pd.DataFrame) -> pd.Series:
    return df.iloc[-2] if len(df) >= 2 else df.iloc[-1]


def 세그먼트(label: str, options: list[str], default: str) -> str:
    try:
        return st.segmented_control(label, options, default=default)
    except Exception:
        idx = options.index(default) if default in options else 0
        return st.radio(label, options, index=idx, horizontal=True)


def 기간_필터(df: pd.DataFrame, period: str) -> pd.DataFrame:
    n = {"7일": 7, "28일": 28, "90일": 90}.get(period, 28)
    return df.tail(min(n, len(df))).copy()


# =============================================================================
# 컴포넌트
# =============================================================================
def 상단바() -> None:
    st.markdown('<div class="topbar">', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2.4, 1.4, 1.0])
    with c1:
        st.markdown('<div class="badge"><span class="dot"></span><span>크리에이터 스튜디오</span></div>', unsafe_allow_html=True)
        st.markdown("<h1 style='margin:10px 0 0 0; line-height:1.05;'>Creator Studio Pro</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='kicker'>{st.session_state.channel} · {st.session_state.plan} 플랜</div>",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown("<div style='font-weight:850; margin:6px 0 10px 0;'>빠른 실행</div>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("📅 예약", use_container_width=True):
                if st.session_state.toast_on:
                    st.toast("예약 완료(데모)", icon="📅")
        with b2:
            if st.button("✅ 게시", use_container_width=True):
                if st.session_state.toast_on:
                    st.toast("게시 완료(데모)", icon="✅")

        with st.popover("✨ 바로가기"):
            st.write("• 초안")
            st.write("• 템플릿")
            st.write("• 내보내기")

    with c3:
        with st.popover("👤 계정"):
            st.write("**채널**")
            st.caption(st.session_state.channel)
            st.divider()
            st.button("채널 전환", use_container_width=True)
            st.button("로그아웃", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()


def KPI(df: pd.DataFrame) -> None:
    latest = df.iloc[-1]
    prev = 이전_행(df)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("조회수", f"{int(latest['views']):,}", f"{int(latest['views'] - prev['views']):+,}")
    with c2:
        st.metric("구독자 증가", f"+{int(latest['subs_gained']):,}", f"{int(latest['subs_gained'] - prev['subs_gained']):+,}")
    with c3:
        st.metric("수익", f"${float(latest['revenue']):,.2f}", f"${(float(latest['revenue'] - prev['revenue'])):+.2f}")
    with c4:
        retention = int(np.clip(60 + (latest["ctr"] - 6.0) * 1.4, 35, 82))
        st.metric("리텐션", f"{retention}%", f"{(retention - 60):+d}%")
        st.progress(retention / 100, text="시청 유지율(데모)")


def 조회수_차트(df: pd.DataFrame) -> None:
    st.session_state.period = 세그먼트("기간", ["7일", "28일", "90일"], st.session_state.period)
    chart_df = 기간_필터(df, st.session_state.period)

    base = alt.Chart(chart_df).encode(
        x=alt.X("date:T", axis=alt.Axis(title=None, format="%b %d", grid=False)),
        tooltip=[
            alt.Tooltip("date:T", title="날짜"),
            alt.Tooltip("views:Q", title="조회수", format=","),
            alt.Tooltip("subs_gained:Q", title="구독자", format=","),
            alt.Tooltip("revenue:Q", title="수익", format=",.2f"),
            alt.Tooltip("ctr:Q", title="CTR", format=".1f"),
            alt.Tooltip("rpm:Q", title="RPM", format=".2f"),
        ],
    )

    area = base.mark_area(
        opacity=0.95,
        line={"color": "#ff2f98"},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(255, 77, 166, 0.50)", offset=0),
                alt.GradientStop(color="rgba(255, 77, 166, 0.02)", offset=1),
            ],
            x1=1,
            x2=1,
            y1=1,
            y2=0,
        ),
    ).encode(y=alt.Y("views:Q", axis=alt.Axis(title=None)))

    spikes = (
        base.transform_filter(alt.datum.is_spike == True)
        .mark_point(size=90, filled=True, color="#ff2f98", opacity=0.95)
        .encode(y="views:Q")
    )

    st.altair_chart((area + spikes).interactive(), use_container_width=True)


def 보조_차트(df: pd.DataFrame) -> None:
    chart_df = 기간_필터(df, st.session_state.period)
    c1, c2 = st.columns(2)

    with c1:
        subs = (
            alt.Chart(chart_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", axis=alt.Axis(title=None, format="%b %d", grid=False)),
                y=alt.Y("subs_gained:Q", axis=alt.Axis(title=None)),
                tooltip=["date:T", "subs_gained:Q"],
            )
            .properties(height=220, title="구독자 증가")
        )
        st.altair_chart(subs, use_container_width=True)

    with c2:
        rev = (
            alt.Chart(chart_df)
            .mark_bar(opacity=0.88, cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("date:T", axis=alt.Axis(title=None, format="%b %d", grid=False)),
                y=alt.Y("revenue:Q", axis=alt.Axis(title=None)),
                tooltip=["date:T", alt.Tooltip("revenue:Q", format=",.2f")],
            )
            .properties(height=220, title="수익")
        )
        st.altair_chart(rev, use_container_width=True)


def 운영_패널() -> None:
    with st.expander("운영", expanded=True):
        t = st.text_input("제목", placeholder="제목을 입력하세요…")
        st.file_uploader("썸네일", type=["png", "jpg", "jpeg"])
        when = st.date_input("예약 날짜", value=datetime.today().date() + timedelta(days=2))

        c1, c2 = st.columns(2)
        with c1:
            if st.button("예약", type="primary", use_container_width=True, disabled=(not t)):
                if st.session_state.toast_on:
                    st.toast(f"예약 완료: {when}", icon="📅")
                st.balloons()
        with c2:
            if st.button("초안 저장", use_container_width=True, disabled=(not t)):
                if st.session_state.toast_on:
                    st.toast("초안 저장 완료", icon="🧾")


def 영상_라이브러리(df_videos: pd.DataFrame) -> None:
    q = st.text_input("검색", placeholder="제목에 포함된 단어…")
    min_views = st.slider("최소 조회수", 0, int(df_videos["조회수"].max()), 10_000, step=5_000)

    filt = df_videos.copy()
    if q.strip():
        filt = filt[filt["영상 제목"].str.contains(q.strip(), case=False, na=False)]
    filt = filt[filt["조회수"] >= min_views].reset_index(drop=True)

    edited = st.data_editor(
        filt,
        column_config={
            "영상 제목": st.column_config.TextColumn("제목", width="large"),
            "조회수": st.column_config.NumberColumn("조회수", format="%d 👁️"),
            "CTR(%)": st.column_config.ProgressColumn("CTR", min_value=0, max_value=20, format="%.1f%%"),
            "수익($)": st.column_config.NumberColumn("수익", format="$%.2f"),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
    )

    st.download_button(
        "CSV 내보내기",
        edited.to_csv(index=False).encode("utf-8-sig"),
        file_name="영상_성과.csv",
        mime="text/csv",
        use_container_width=True,
    )


def 댓글_모듈(seed: int) -> None:
    rng = np.random.default_rng(int(seed))
    labels = ["긍정", "중립", "부정"]
    vals = rng.integers(18, 70, size=3).astype(int)
    cdf = pd.DataFrame({"감성": labels, "건수": vals})

    bar = (
        alt.Chart(cdf)
        .mark_bar(opacity=0.92, cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("감성:N", title=None),
            y=alt.Y("건수:Q", title=None),
            tooltip=["감성:N", "건수:Q"],
            color=alt.Color(
                "감성:N",
                scale=alt.Scale(domain=labels, range=["#ff4da6", "#ff9bd4", "#ff2f98"]),
                legend=None,
            ),
        )
        .properties(height=240)
    )
    st.altair_chart(bar, use_container_width=True)

    with st.expander("키워드(데모)", expanded=False):
        st.write("`좋아요`, `튜토리얼`, `워크플로우`, `감사합니다`, `예쁘다`, `더 올려주세요`")


# =============================================================================
# 페이지
# =============================================================================
def 대시보드(df: pd.DataFrame) -> None:
    st.markdown("### 채널 성과")
    KPI(df)

    st.write("")
    c_main, c_side = st.columns([2.2, 1.2])

    with c_main:
        st.markdown("#### 조회수 추이")
        조회수_차트(df)
        st.write("")
        보조_차트(df)

    with c_side:
        운영_패널()
        with st.popover("메모"):
            st.write("스파이크 마커 = 상위 5% 조회수(데모)")
            st.write("운영 단계에서는 이동평균/이상치 알림을 추가하면 좋아요.")


def 콘텐츠_매니저(df_videos: pd.DataFrame) -> None:
    st.title("콘텐츠 매니저")
    t1, t2 = st.tabs(["영상 라이브러리", "댓글 분석"])
    with t1:
        영상_라이브러리(df_videos)
    with t2:
        댓글_모듈(seed=int(st.session_state.seed) + 99)


def 설정() -> None:
    st.title("설정")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("알림")
        st.toggle("주간 이메일 요약", value=True)
        st.toggle("마일스톤 알림", value=True)
        st.toggle("업로드 리마인더", value=False)

    with c2:
        st.subheader("연동")
        st.text_input("YouTube Data API 키", type="password", placeholder="••••••••••••")
        st.checkbox("캐시 사용", value=True)
        st.checkbox("상세 로그", value=False)

    if st.button("저장", type="primary"):
        if st.session_state.toast_on:
            st.toast("저장 완료", icon="✅")


# =============================================================================
# 사이드바 / 앱
# =============================================================================
def 상태_초기화() -> None:
    st.session_state.setdefault("menu", "대시보드")
    st.session_state.setdefault("days", 90)
    st.session_state.setdefault("seed", 42)
    st.session_state.setdefault("period", "28일")
    st.session_state.setdefault("toast_on", True)
    st.session_state.setdefault("plan", "Pro")
    st.session_state.setdefault("channel", "Tech Creator")


def 사이드바() -> str:
    with st.sidebar:
        st.header("🎛️ 컨트롤 센터")

        st.session_state.menu = st.radio(
            "메뉴",
            ["대시보드", "콘텐츠 매니저", "설정"],
            index=["대시보드", "콘텐츠 매니저", "설정"].index(st.session_state.menu),
            label_visibility="collapsed",
        )

        st.divider()
        st.subheader("시뮬레이션")
        st.session_state.days = st.slider("분석 기간(일)", 30, 180, int(st.session_state.days), step=5)
        st.session_state.seed = st.number_input("시드(seed)", 0, 9999, int(st.session_state.seed), step=1)

        st.divider()
        st.subheader("UX")
        st.session_state.toast_on = st.toggle("토스트 알림", value=bool(st.session_state.toast_on))
        fx = st.selectbox("이펙트", ["없음", "풍선", "눈"], index=0)

        if st.button("동기화(데모)", use_container_width=True):
            with st.status("동기화 중…", expanded=True) as status:
                st.write("연결")
                st.progress(25)
                time.sleep(0.15)
                st.write("데이터 가져오기")
                st.progress(65)
                time.sleep(0.15)
                st.write("마무리")
                st.progress(100)
                status.update(label="완료", state="complete", expanded=False)

            if st.session_state.toast_on:
                st.toast("동기화 완료", icon="💗")

        if fx == "풍선":
            st.balloons()
        elif fx == "눈":
            st.snow()

        st.divider()
        st.caption("Creator Studio Pro · 핑크 라이트")

    return st.session_state.menu


def main() -> None:
    상태_초기화()
    스타일_적용()
    알테어_테마_등록()

    menu = 사이드바()

    df_analytics = 채널_데이터_생성(int(st.session_state.days), int(st.session_state.seed))
    df_videos = 영상_목록_생성(count=12, seed=int(st.session_state.seed) + 7)

    상단바()

    if menu == "대시보드":
        대시보드(df_analytics)
    elif menu == "콘텐츠 매니저":
        콘텐츠_매니저(df_videos)
    else:
        설정()

    st.divider()
    st.caption("Streamlit · Altair · Pink Light UI")


if __name__ == "__main__":
    main()
