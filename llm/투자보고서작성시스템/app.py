from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

try:
    from investment_report import investment_report
except ImportError:
    from report_service.investment_report import investment_report

try:
    from stock_search import stock_search
except ImportError:
    from search.stock_search import stock_search

try:
    from stock_info import Stock
except ImportError:
    from stock_info.stock_info import Stock


STATUS_PRESETS = {
    "초행 탐험가": "처음 보는 종목이라 지형부터 파악해야 하는 초행 탐험가",
    "단기 레이더": "짧은 구간의 모멘텀과 변동성을 빠르게 읽어야 하는 단기 레이더",
    "장기 수집가": "오래 들고 갈 만한 본체인지 차분히 점검하는 장기 수집가",
    "보스전 브리퍼": "회의실에서 바로 설명해야 해서 핵심만 압축해야 하는 보스전 브리퍼",
    "직접 입력": "",
}

GOAL_PRESETS = {
    "매수 루트 개방": "지금 진입해도 되는지 판단할 매수 루트를 개방",
    "리스크 함정 해제": "지금 피해야 할 위험 요인을 먼저 해제",
    "보스전 브리핑 확보": "임원 보고 직전, 핵심만 압축한 보스전 브리핑 확보",
    "비교 덱 정리": "다른 종목과 바로 비교할 수 있는 기준 덱 정리",
    "직접 입력": "",
}

QUESTION_PRESETS = {
    "강점/약점 스캔": "이 종목의 강점과 약점을 한 번에 스캔해줘",
    "최근 턴 분석": "최근 분기 흐름이 회복 중인지 꺾이는 중인지 냉정하게 판정해줘",
    "진입 타이밍 판정": "지금 진입이 공격적인지 방어적인지 판정해줘",
    "간부 보고 10줄": "회의실에서 바로 읽을 수 있게 10줄 안쪽으로 요약해줘",
    "직접 입력": "",
}

REACTION_PRESETS = {
    "작전판 들이밀기": "작전판을 들이밀며 빠르게 결론부터 말해 달라고 한다",
    "메모장 펼치기": "메모장을 펼치고 한 줄도 놓치지 않겠다는 얼굴로 바라본다",
    "긴급 호출": "회의 10분 전이라며 핵심만 먼저 던져 달라고 재촉한다",
    "차분한 동행": "서류를 정리해두고 차분하게 끝까지 같이 보자고 한다",
    "직접 입력": "",
}


@dataclass(frozen=True)
class SearchResult:
    symbol: str
    name: str
    exchange: str = "NASDAQ"

    def __str__(self) -> str:
        return f"{self.symbol} · {self.name}"


BASIC_INFO_LABELS = {
    "symbol": "티커",
    "longName": "기업명",
    "industry": "산업",
    "sector": "섹터",
    "marketCap": "시가총액",
    "sharesOutstanding": "발행주식수",
    "currentPrice": "현재가",
    "trailingPE": "PER(TTM)",
    "fiftyTwoWeekHigh": "52주 최고가",
    "fiftyTwoWeekLow": "52주 최저가",
}

FINANCIAL_LABELS = {
    "Total Revenue": "매출액",
    "Gross Profit": "매출총이익",
    "Operating Income": "영업이익",
    "Net Income": "순이익",
    "Total Assets": "자산총계",
    "Total Liabilities Net Minority Interest": "부채총계",
    "Stockholders Equity": "자본총계",
    "Operating Cash Flow": "영업활동현금흐름",
    "Investing Cash Flow": "투자활동현금흐름",
    "Financing Cash Flow": "재무활동현금흐름",
}

FINANCIAL_SECTION_LABELS = {
    "Quarterly Income Statement": "손익계산서",
    "Quarterly Balance Sheet": "재무상태표",
    "Quarterly Cash Flow": "현금흐름표",
}

EXPRESSION_FILES = {
    "smile": ["erika_smile.png"],
    "thinking": ["erika_thinking.png"],
    "pout": ["erika_pout.png"],
    "surprised": ["erika_surprised.png"],
}

STAGE_LABELS = {
    "search": "종목 수색",
    "brief": "작전 세팅",
    "data": "장부 확인",
    "report": "최종 보고",
}


def _load_env() -> None:
    current = Path(__file__).resolve()
    for candidate in (
        current.parent / ".env",
        current.parent.parent / ".env",
        current.parent.parent.parent / ".env",
    ):
        if candidate.exists():
            load_dotenv(candidate, override=False)


_load_env()

st.set_page_config(
    page_title="에리카와 대화하는 투자 리포트",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _expression_asset_path(expression: str) -> Path | None:
    base_dirs = [Path(__file__).resolve().parent, Path.cwd()]
    for directory in base_dirs:
        for filename in EXPRESSION_FILES.get(expression, []):
            candidate = directory / filename
            if candidate.exists():
                return candidate
    return None


def _image_data_uri(path: Path | None) -> str | None:
    if path is None:
        return None
    ext = path.suffix.lower().replace('.', '') or 'jpeg'
    mime = 'image/jpeg' if ext in {'jpg', 'jpeg'} else f'image/{ext}'
    encoded = base64.b64encode(path.read_bytes()).decode('utf-8')
    return f'data:{mime};base64,{encoded}'


def _html_block(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(255, 233, 241, 0.92), transparent 22%),
                radial-gradient(circle at 88% 6%, rgba(255, 245, 249, 0.95), transparent 18%),
                linear-gradient(180deg, #fff9fc 0%, #fff3f8 50%, #fffafc 100%);
        }

        [data-testid="stHeader"], [data-testid="stToolbar"] {
            background: transparent;
        }

        [data-testid="collapsedControl"] {
            display: none;
        }

        .block-container {
            max-width: 1280px;
            padding-top: 1rem;
            padding-bottom: 1.2rem;
        }

        .petal {
            position: fixed;
            z-index: 0;
            opacity: .15;
            pointer-events: none;
            animation: drift linear infinite;
            font-size: 1.3rem;
        }

        .p1 { left: 4%; top: 5%; animation-duration: 15s; }
        .p2 { left: 22%; top: -2%; animation-duration: 19s; }
        .p3 { left: 76%; top: 4%; animation-duration: 17s; }
        .p4 { left: 92%; top: 8%; animation-duration: 16s; }

        @keyframes drift {
            0% { transform: translateY(-20px) translateX(0) rotate(0deg); }
            50% { transform: translateY(44vh) translateX(18px) rotate(140deg); }
            100% { transform: translateY(90vh) translateX(-12px) rotate(280deg); }
        }

        .hero-shell {
            position: relative;
            z-index: 1;
            padding: 1rem 1.15rem;
            border-radius: 26px;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.93), rgba(255,243,248,0.9));
            border: 1px solid rgba(218, 136, 168, 0.16);
            box-shadow: 0 18px 54px rgba(190, 116, 145, 0.10);
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 800;
            color: #432534;
            line-height: 1.15;
            margin-bottom: .25rem;
        }

        .hero-copy {
            color: #704c5a;
            font-size: .98rem;
            line-height: 1.65;
        }

        .hero-copy b {
            color: #b2507a;
        }

        .app-shell [data-testid="stVerticalBlockBorderWrapper"] {
            position: relative;
            z-index: 1;
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(218, 136, 168, 0.16);
            border-radius: 28px;
            box-shadow: 0 18px 54px rgba(190, 116, 145, 0.10);
            padding: 1rem;
            backdrop-filter: blur(10px);
        }

        .left-shell [data-testid="stVerticalBlockBorderWrapper"] {
            overflow: hidden;
        }

        .right-shell [data-testid="stVerticalBlockBorderWrapper"] {
            min-height: 80vh;
        }

        .portrait-card {
            margin-bottom: .95rem;
            border-radius: 24px;
            overflow: hidden;
            background: linear-gradient(180deg, #fff0f6, #fff9fc);
            border: 1px solid rgba(218, 136, 168, 0.18);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
        }

        .portrait-card img {
            width: 100%;
            display: block;
        }

        .label-row {
            display: flex;
            flex-wrap: wrap;
            gap: .5rem;
            margin-bottom: .8rem;
        }

        .label-chip {
            padding: .4rem .72rem;
            border-radius: 999px;
            background: #fff3f8;
            color: #b54b79;
            border: 1px solid rgba(218, 136, 168, 0.16);
            font-size: .8rem;
            font-weight: 800;
        }

        .section-title {
            font-size: 1.08rem;
            font-weight: 800;
            color: #442534;
            margin: .25rem 0 .45rem 0;
        }

        .section-copy {
            color: #6d4c5b;
            line-height: 1.65;
            font-size: .95rem;
            margin-bottom: .85rem;
        }

        .status-card {
            border-radius: 18px;
            padding: .9rem 1rem;
            background: linear-gradient(180deg, #fff8fb, #fff2f7);
            border: 1px solid rgba(218, 136, 168, 0.14);
            margin-bottom: .9rem;
            color: #6d4c5b;
            line-height: 1.6;
        }

        .status-strong {
            color: #432534;
            font-weight: 800;
        }

        .meter-wrap {
            margin: .72rem 0;
        }

        .meter-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: .36rem;
            font-size: .86rem;
            color: #6d4c5b;
            font-weight: 700;
        }

        .meter-track {
            height: 10px;
            border-radius: 999px;
            background: #f6e7ee;
            overflow: hidden;
            border: 1px solid rgba(218, 136, 168, 0.10);
        }

        .meter-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #f39ab8 0%, #d86a95 100%);
        }

        .reaction-card {
            margin-top: .85rem;
            padding: .85rem .95rem;
            border-radius: 18px;
            background: linear-gradient(180deg, #fffafb, #fff5f8);
            border: 1px solid rgba(218, 136, 168, 0.13);
            color: #6d4c5b;
            line-height: 1.6;
            font-size: .93rem;
        }

        .stage-row {
            display: flex;
            flex-wrap: wrap;
            gap: .5rem;
            margin-bottom: .85rem;
        }

        .stage-chip {
            padding: .44rem .72rem;
            border-radius: 999px;
            background: #fff3f8;
            border: 1px solid rgba(218, 136, 168, 0.14);
            color: #b54b79;
            font-size: .82rem;
            font-weight: 800;
        }

        .stage-chip.current {
            background: linear-gradient(180deg, #ffedf5, #ffe4ef);
            box-shadow: inset 0 0 0 1px rgba(218, 136, 168, 0.12);
        }

        .bubble {
            max-width: 92%;
            padding: .9rem 1rem;
            border-radius: 20px;
            line-height: 1.68;
            margin-bottom: .7rem;
            box-shadow: 0 8px 22px rgba(190, 116, 145, 0.08);
            font-size: .97rem;
        }

        .bubble.erika {
            background: linear-gradient(180deg, #fff6fa, #fff1f6);
            border: 1px solid rgba(218, 136, 168, 0.14);
            color: #5f3d4a;
            margin-right: auto;
        }

        .bubble.user {
            background: linear-gradient(180deg, #f4f8ff, #eef5ff);
            border: 1px solid rgba(120, 148, 218, 0.16);
            color: #34455d;
            margin-left: auto;
        }

        .bubble-label {
            display: inline-block;
            font-size: .76rem;
            font-weight: 800;
            margin-bottom: .3rem;
            opacity: .78;
        }

        .minor-note {
            color: #8a6877;
            font-size: .84rem;
        }

        .report-shell {
            border-radius: 24px;
            padding: 1.08rem;
            background: linear-gradient(180deg, #fffdfd, #fff7fb);
            border: 1px solid rgba(218, 136, 168, 0.14);
        }

        div[data-testid="stTabs"] button[role="tab"] {
            border-radius: 999px;
            padding-inline: .95rem;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(218, 136, 168, 0.1);
        }

        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 16px !important;
            border: 1px solid rgba(196, 120, 151, 0.16) !important;
            background: linear-gradient(180deg, #fffdfd 0%, #fff5f8 100%) !important;
            color: #5d3b49 !important;
            font-weight: 700 !important;
            min-height: 2.8rem !important;
            box-shadow: 0 8px 18px rgba(190, 116, 145, 0.06);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: rgba(196, 120, 151, 0.28) !important;
            color: #4c2c39 !important;
        }

        .stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: linear-gradient(180deg, #f07eac 0%, #dc6793 100%) !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 14px 26px rgba(220, 103, 147, 0.18) !important;
        }

        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
        .stRadio label, .stMultiSelect div[data-baseweb="select"] > div {
            border-radius: 16px !important;
        }

        .stRadio > div {
            gap: .4rem;
        }

        .stRadio label {
            padding: .65rem .8rem !important;
            border: 1px solid rgba(218, 136, 168, 0.12) !important;
            background: #fff9fc !important;
        }
        </style>

        <div class="petal p1">🌸</div>
        <div class="petal p2">✿</div>
        <div class="petal p3">🌸</div>
        <div class="petal p4">✿</div>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    _html_block(
        """
        <div class="hero-shell">
            <div class="hero-title">에리카와 대화하는 투자 리포트</div>
            <div class="hero-copy"><b>종목</b>만 찍어. 장부는 내가 훑고, 결론은 내가 정리해. 다만 너무 부려먹을 생각은 하지 마.</div>
        </div>
        """
    )


def _init_state() -> None:
    defaults = {
        "stage": "search",
        "search_query": "Apple",
        "search_hits": [],
        "search_feedback": None,
        "selected_symbol": None,
        "selected_name": None,
        "selected_exchange": None,
        "basic_frame": None,
        "financial_frames": None,
        "basic_info_markdown": None,
        "financial_markdown": None,
        "latest_report": None,
        "latest_report_symbol": None,
        "status": STATUS_PRESETS["초행 탐험가"],
        "goal": GOAL_PRESETS["매수 루트 개방"],
        "question": QUESTION_PRESETS["강점/약점 스캔"],
        "reaction_trigger": REACTION_PRESETS["작전판 들이밀기"],
        "pet_hunger": 68,
        "pet_affinity": 62,
        "pet_focus": 71,
        "pet_energy": 64,
        "pet_expression": "thinking",
        "pet_message": "흥, 늦진 않았네. 종목만 던져. 쓸 만한 숫자는 내가 골라낼 테니까.",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


_init_state()


def _set_stage(stage: str) -> None:
    st.session_state["stage"] = stage


def _select_preset(label: str, options: dict[str, str], key: str, custom_label: str) -> str:
    choice_key = f"{key}_choice"
    current_value = st.session_state.get(key, "")
    matched_choice = next((name for name, value in options.items() if value == current_value and name != "직접 입력"), "직접 입력")
    current_choice = st.session_state.get(choice_key, matched_choice)
    choice = st.selectbox(label, list(options.keys()), index=list(options.keys()).index(current_choice), key=choice_key)
    if choice == "직접 입력":
        value = st.text_input(custom_label, value=current_value if matched_choice == "직접 입력" else "", key=f"{key}_custom")
    else:
        value = options[choice]
    st.session_state[key] = value
    return value


def _translate_basic_frame(frame):
    translated = frame.copy()
    if "항목" in translated.columns:
        translated["항목"] = translated["항목"].map(lambda x: BASIC_INFO_LABELS.get(str(x), str(x)))
    if "Value" in translated.columns:
        translated = translated.rename(columns={"Value": "값"})
    return translated


def _translate_financial_frame(frame):
    if frame is None:
        return frame
    translated = frame.copy()
    translated.index = [FINANCIAL_LABELS.get(str(idx), str(idx)) for idx in translated.index]
    translated.index.name = "항목"
    return translated


def _financials_to_markdown(financial_frames: dict[str, Any]) -> str:
    sections = []
    for key in [
        "Quarterly Income Statement",
        "Quarterly Balance Sheet",
        "Quarterly Cash Flow",
    ]:
        frame = financial_frames.get(key)
        title = FINANCIAL_SECTION_LABELS.get(key, key)
        if frame is None:
            sections.append(f"### {title}\n| 데이터 없음 |\n|---|")
        else:
            sections.append(f"### {title}\n{frame.to_markdown()}")
    return "\n\n".join(sections)


def _bubble(speaker: str, text: str) -> None:
    who = "에리카" if speaker == "erika" else "당신"
    cls = "erika" if speaker == "erika" else "user"
    _html_block(
        f"""
        <div class="bubble {cls}">
            <div class="bubble-label">{who}</div>
            <div>{text}</div>
        </div>
        """
    )


def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def _wear_down(reason: str) -> None:
    hunger = int(st.session_state.get("pet_hunger", 60))
    affinity = int(st.session_state.get("pet_affinity", 60))
    focus = int(st.session_state.get("pet_focus", 60))
    energy = int(st.session_state.get("pet_energy", 60))

    if reason == "search":
        hunger -= 2
        energy -= 1
    elif reason == "analyze":
        hunger -= 4
        affinity -= 1
        focus += 4
        energy -= 3
    elif reason == "report":
        hunger -= 5
        affinity -= 2
        focus += 5
        energy -= 4
    elif reason == "idle":
        hunger -= 3
        affinity -= 4
        focus -= 2
        energy -= 2
    elif reason == "move":
        hunger -= 1
        affinity -= 1
        energy -= 1

    st.session_state["pet_hunger"] = _clamp(hunger)
    st.session_state["pet_affinity"] = _clamp(affinity)
    st.session_state["pet_focus"] = _clamp(focus)
    st.session_state["pet_energy"] = _clamp(energy)

    if st.session_state["pet_affinity"] <= 28:
        st.session_state["pet_expression"] = "pout"
        st.session_state["pet_message"] = "흥, 말만 시키고 챙기질 않네. 이 정도면 삐질 만하지 않아?"
    elif st.session_state["pet_hunger"] <= 24:
        st.session_state["pet_expression"] = "pout"
        st.session_state["pet_message"] = "잠깐. 공복 상태로 숫자 읽으라고? 효율이 떨어지는 게 당연하잖아."


def _render_meter(label: str, value: int) -> None:
    _html_block(
        f"""
        <div class="meter-wrap">
            <div class="meter-head"><span>{label}</span><span>{value}</span></div>
            <div class="meter-track"><div class="meter-fill" style="width:{value}%"></div></div>
        </div>
        """
    )


def _portrait_html(expression: str) -> None:
    image_uri = _image_data_uri(_expression_asset_path(expression))
    if image_uri:
        _html_block(
            f"""
            <div class="portrait-card">
                <img src="{image_uri}" alt="에리카 표정">
            </div>
            """
        )
    else:
        _html_block("<div class='portrait-card' style='aspect-ratio:4/5.8;'></div>")


def _pet_action(action: str) -> None:
    hunger = int(st.session_state.get("pet_hunger", 60))
    affinity = int(st.session_state.get("pet_affinity", 60))
    focus = int(st.session_state.get("pet_focus", 60))
    energy = int(st.session_state.get("pet_energy", 60))

    if action == "feed":
        hunger = _clamp(hunger + 18)
        affinity = _clamp(affinity + 6)
        energy = _clamp(energy + 2)
        expression = "smile"
        message = "좋아. 이 정도면 성의는 인정해 줄게. 오늘은 좀 더 잘 봐주지."
    elif action == "praise":
        affinity = _clamp(affinity + 13)
        focus = _clamp(focus + 2)
        expression = "smile"
        message = "칭찬이 과하긴 한데... 뭐, 싫지는 않아. 한 번만 더 해도 봐줄게."
    elif action == "analyze":
        focus = _clamp(focus + 15)
        hunger = _clamp(hunger - 5)
        affinity = _clamp(affinity - 1)
        energy = _clamp(energy - 4)
        expression = "thinking"
        message = "좋아. 수다는 여기까지. 이제 장부부터 베어 보자."
    elif action == "rest":
        energy = _clamp(energy + 16)
        affinity = _clamp(affinity + 3)
        focus = _clamp(focus + 4)
        expression = "smile"
        message = "응, 이건 마음에 드네. 잠깐 숨 돌리고 나면 판단도 덜 흐려져."
    else:
        hunger = _clamp(hunger - 6)
        affinity = _clamp(affinity - 10)
        focus = _clamp(focus - 5)
        energy = _clamp(energy - 4)
        expression = "pout"
        message = "방치해? 제법인데. 좋아, 나도 이제 안 봐준다."

    st.session_state["pet_hunger"] = hunger
    st.session_state["pet_affinity"] = affinity
    st.session_state["pet_focus"] = focus
    st.session_state["pet_energy"] = energy
    st.session_state["pet_expression"] = expression
    st.session_state["pet_message"] = message


def _auto_expression() -> None:
    stage = st.session_state.get("stage", "search")
    affinity = int(st.session_state.get("pet_affinity", 60))
    if affinity <= 28:
        st.session_state["pet_expression"] = "pout"
        return
    if stage == "data":
        st.session_state["pet_expression"] = "thinking"
    elif stage == "report":
        st.session_state["pet_expression"] = "smile" if affinity >= 60 else "thinking"
    elif stage == "search" and (st.session_state.get("search_feedback") or {}).get("source") == "fallback":
        st.session_state["pet_expression"] = "pout"
    elif stage == "brief":
        st.session_state["pet_expression"] = "thinking"


def _render_left_panel() -> None:
    _auto_expression()
    available = any(_expression_asset_path(name) is not None for name in EXPRESSION_FILES)
    expression = st.session_state.get("pet_expression", "thinking")
    _portrait_html(expression)


    selected_name = st.session_state.get("selected_name") or "아직 선택 전"
    selected_symbol = st.session_state.get("selected_symbol") or "-"
    stage_label = STAGE_LABELS.get(st.session_state.get("stage"), "종목 찾기")
    _html_block(
        f"""
        <div class="section-title">에리카 컨디션</div><div class="minor-note">너무 오래 방치하면 호감도도 같이 빠져. 적당히 챙겨.</div>
        """
    )

    _render_meter("포만감", int(st.session_state.get("pet_hunger", 0)))
    _render_meter("호감도", int(st.session_state.get("pet_affinity", 0)))
    _render_meter("집중도", int(st.session_state.get("pet_focus", 0)))
    _render_meter("체력", int(st.session_state.get("pet_energy", 0)))

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        if st.button("🍙 간식 건네기", use_container_width=True):
            _pet_action("feed")
            st.rerun()
    with r1c2:
        if st.button("✨ 쓰다듬기", use_container_width=True):
            _pet_action("praise")
            st.rerun()

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        if st.button("📊 분석 돌입", use_container_width=True):
            _pet_action("analyze")
            st.rerun()
    with r2c2:
        if st.button("🛏 쉬게 하기", use_container_width=True):
            _pet_action("rest")
            st.rerun()

    if st.button("🫥 방치하기", use_container_width=True):
        _pet_action("ignore")
        st.rerun()

    _html_block(f"<div class='reaction-card'>{st.session_state.get('pet_message', '')}</div>")

    if not available:
        st.warning("같은 폴더에 표정 이미지 4종을 두면 에리카 얼굴이 제대로 살아나.")


def _perform_search(query: str) -> None:
    result = stock_search(query)
    hits = [
        SearchResult(symbol=hit["symbol"], name=hit["name"], exchange=hit.get("exchange", "NASDAQ"))
        for hit in result.get("hits", [])
    ]
    st.session_state["search_query"] = query
    st.session_state["search_hits"] = hits
    st.session_state["search_feedback"] = result


def _load_stock_data(symbol: str, name: str, exchange: str) -> None:
    stock = Stock(symbol)
    basic_frame = _translate_basic_frame(stock.get_basic_info_frame())
    raw_financial_frames = stock.get_financial_statement_frames()
    financial_frames = {key: _translate_financial_frame(frame) for key, frame in raw_financial_frames.items()}
    st.session_state["selected_symbol"] = symbol
    st.session_state["selected_name"] = name
    st.session_state["selected_exchange"] = exchange
    st.session_state["basic_frame"] = basic_frame
    st.session_state["financial_frames"] = financial_frames
    st.session_state["basic_info_markdown"] = basic_frame.to_markdown(index=False)
    st.session_state["financial_markdown"] = _financials_to_markdown(financial_frames)


def _render_stage_nav() -> None:
    current = st.session_state.get("stage", "search")
    chips = []
    for key in ["search", "brief", "data", "report"]:
        cls = "stage-chip current" if key == current else "stage-chip"
        chips.append(f"<div class='{cls}'>{STAGE_LABELS[key]}</div>")
    _html_block(f"<div class='stage-row'>{''.join(chips)}</div>")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("종목 수색", use_container_width=True):
            _wear_down("move")
            _set_stage("search")
            st.rerun()
    with c2:
        if st.button("작전 세팅", use_container_width=True, disabled=st.session_state.get("selected_symbol") is None):
            _wear_down("move")
            _set_stage("brief")
            st.rerun()
    with c3:
        if st.button("장부 확인", use_container_width=True, disabled=st.session_state.get("basic_frame") is None):
            _wear_down("move")
            _set_stage("data")
            st.rerun()
    with c4:
        if st.button("최종 보고", use_container_width=True, disabled=st.session_state.get("latest_report") is None):
            _wear_down("move")
            _set_stage("report")
            st.rerun()


def _render_search_stage() -> None:
    _bubble("erika", "종목명이나 티커부터 내놔. 내가 후보를 걸러줄게. 넓게 휘젓는다고 답이 나오는 건 아니니까.")

    with st.form("search_form", clear_on_submit=False):
        query = st.text_input("회사명 또는 티커", value=st.session_state.get("search_query", "Apple"), placeholder="예: Apple, AAPL, NVIDIA")
        submitted = st.form_submit_button("후보 수색 시작", use_container_width=True)
        if submitted:
            _wear_down("search")
            _perform_search(query)

    feedback = st.session_state.get("search_feedback")
    if feedback:
        if feedback.get("source") == "fallback":
            st.warning(feedback.get("message", "흥, 검색 엔진이 잠깐 삐걱댔어. 그래도 대체 후보는 챙겨놨으니까 그중에서 골라."))
        elif feedback.get("source") != "empty":
            st.info(feedback.get("message", "좋아. 후보군은 정리했어."))

    hits: list[SearchResult] = st.session_state.get("search_hits", [])
    if hits:
        _bubble("erika", "후보를 하나 찍어. 선택만 끝나면 내가 장부부터 바로 열어볼 테니까.")
        selected = st.radio(
            "검색 결과",
            hits,
            index=0,
            horizontal=False,
            format_func=lambda item: f"{item.symbol} · {item.name} ({item.exchange})",
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("이 종목 찜하기", type="primary", use_container_width=True):
                try:
                    with st.spinner("에리카가 장부를 끌어오는 중이야..."):
                        _wear_down("analyze")
                        _load_stock_data(selected.symbol, selected.name, selected.exchange)
                    _set_stage("brief")
                    st.rerun()
                except Exception as exc:
                    st.error(f"종목 데이터를 불러오다가 문제가 생겼어: {exc}")
        with col2:
            st.caption("찜해 두면 다음 칸에서 작전 성격을 정할 수 있어.")
    else:
        st.caption("아직 후보가 없으면 위에서 종목명이나 티커부터 던져.")


def _render_brief_stage() -> None:
    selected_name = st.session_state.get("selected_name")
    selected_symbol = st.session_state.get("selected_symbol")
    if not selected_symbol:
        st.info("먼저 종목을 선택해줘.")
        return

    _bubble("user", f"이번 판은 {selected_name}({selected_symbol})를 보고 싶어.")
    _bubble("erika", "좋아. 이제 작전만 정하자. 네 목적이 뭐냐에 따라 내가 찌르는 포인트도 달라지니까.")

    col1, col2 = st.columns(2)
    with col1:
        st.caption("지금 네 포지션부터 정해.")
        status = _select_preset("현재 스테이터스", STATUS_PRESETS, "status", "직접 스테이터스 입력")
        st.caption("내가 어느 각도로 칼을 들이밀지 정하는 질문이야.")
        question = _select_preset("에리카에게 던질 질문", QUESTION_PRESETS, "question", "직접 질문 입력")
    with col2:
        st.caption("이번 판의 승리 조건이라고 생각하면 돼.")
        goal = _select_preset("최종 퀘스트", GOAL_PRESETS, "goal", "직접 퀘스트 입력")
        st.caption("네 태도 하나로 대화 템포도 좀 달라지거든.")
        reaction_trigger = _select_preset("행동 트리거", REACTION_PRESETS, "reaction_trigger", "직접 트리거 입력")

    _bubble("erika", "세팅은 끝났어. 이제 장부부터 깔지, 바로 최종 보고를 뽑을지 정해.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("장부 먼저 열기", type="primary", use_container_width=True):
            _set_stage("data")
            st.rerun()
    with c2:
        if st.button("최종 보고 바로 뽑기", use_container_width=True):
            try:
                with st.spinner("에리카가 결론 문장까지 다듬는 중이야..."):
                    _wear_down("report")
                    report = investment_report(
                        company=selected_name,
                        symbol=selected_symbol,
                        basic_info=st.session_state["basic_info_markdown"],
                        financials=st.session_state["financial_markdown"],
                        status=status,
                        goal=goal,
                        question=question,
                        reaction_trigger=reaction_trigger,
                    )
                st.session_state["latest_report"] = report
                st.session_state["latest_report_symbol"] = selected_symbol
                _set_stage("report")
                st.rerun()
            except Exception as exc:
                st.error(f"흥, 보고서 쓰다가 꼬였네: {exc}")


def _render_data_stage() -> None:
    basic_frame = st.session_state.get("basic_frame")
    financial_frames = st.session_state.get("financial_frames") or {}
    selected_name = st.session_state.get("selected_name")
    selected_symbol = st.session_state.get("selected_symbol")
    if basic_frame is None:
        st.info("먼저 종목을 선택해줘.")
        return

    _bubble("erika", f"좋아. {selected_name}의 체급이랑 최근 분기 흐름부터 보자. 여기서 결이 잡혀야 최종 판정도 덜 흔들려.")

    tabs = st.tabs(["기본 정보", "손익계산서", "재무상태표", "현금흐름표"])
    with tabs[0]:
        st.dataframe(basic_frame, use_container_width=True, hide_index=True, height=360)
    tab_keys = [
        "Quarterly Income Statement",
        "Quarterly Balance Sheet",
        "Quarterly Cash Flow",
    ]
    for idx, title in enumerate(tab_keys, start=1):
        with tabs[idx]:
            frame = financial_frames.get(title)
            if frame is not None:
                st.dataframe(frame, use_container_width=True, height=360)
            else:
                st.info("데이터가 비어 있어.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("최종 보고 작성", type="primary", use_container_width=True):
            try:
                with st.spinner("에리카가 장부를 문장으로 압축하는 중이야..."):
                    _wear_down("report")
                    report = investment_report(
                        company=selected_name,
                        symbol=selected_symbol,
                        basic_info=st.session_state["basic_info_markdown"],
                        financials=st.session_state["financial_markdown"],
                        status=st.session_state["status"],
                        goal=st.session_state["goal"],
                        question=st.session_state["question"],
                        reaction_trigger=st.session_state["reaction_trigger"],
                    )
                st.session_state["latest_report"] = report
                st.session_state["latest_report_symbol"] = selected_symbol
                _set_stage("report")
                st.rerun()
            except Exception as exc:
                st.error(f"흥, 보고서 쓰다가 꼬였네: {exc}")
    with c2:
        if st.button("작전 세팅으로 복귀", use_container_width=True):
            _set_stage("brief")
            st.rerun()


def _render_report_stage() -> None:
    report = st.session_state.get("latest_report")
    symbol = st.session_state.get("latest_report_symbol")
    name = st.session_state.get("selected_name")
    if not report:
        st.info("아직 생성된 보고서가 없어.")
        return

    _bubble("user", f"좋아, 이제 {name}({symbol}) 최종 보고를 보여줘.")
    _bubble("erika", "여기까지 왔으면 결론을 읽어. 다만 들뜨진 마. 확신은 문장이 아니라 숫자에서 가져오는 거니까.")
    _html_block("<div class='report-shell'>")
    st.markdown(report)
    _html_block("</div>")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("장부 다시 보기", use_container_width=True):
            _set_stage("data")
            st.rerun()
    with c2:
        if st.button("세팅 바꿔서 재작성", use_container_width=True):
            _set_stage("brief")
            st.rerun()
    with c3:
        if st.button("새 종목으로 처음부터", use_container_width=True):
            for key in [
                "search_hits", "search_feedback", "selected_symbol", "selected_name", "selected_exchange",
                "basic_frame", "financial_frames", "basic_info_markdown", "financial_markdown",
                "latest_report", "latest_report_symbol",
            ]:
                st.session_state[key] = None if key not in {"search_hits"} else []
            st.session_state["stage"] = "search"
            st.rerun()


def main() -> None:
    _apply_theme()
    _render_header()
    _html_block("<div class='app-shell'>")
    left, right = st.columns([0.9, 1.55], gap="large")
    with left:
        _html_block("<div class='left-shell'>")
        with st.container(border=True):
            _render_left_panel()
        _html_block("</div>")
    with right:
        _html_block("<div class='right-shell'>")
        with st.container(border=True):
            _render_stage_nav()
            stage = st.session_state.get("stage", "search")
            if stage == "search":
                _render_search_stage()
            elif stage == "brief":
                _render_brief_stage()
            elif stage == "data":
                _render_data_stage()
            else:
                _render_report_stage()
        _html_block("</div>")
    _html_block("</div>")


if __name__ == "__main__":
    main()
