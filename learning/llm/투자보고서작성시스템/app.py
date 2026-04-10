from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
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
    "처음 보는 종목": "처음 검토하는 종목이라 사업 구조와 재무 체력을 빠르게 파악해야 합니다.",
    "실적 점검": "최근 분기 실적 흐름이 개선되는지 악화되는지 점검하고 싶습니다.",
    "장기 후보 검토": "장기 보유 후보로 적합한지 경쟁력과 리스크를 균형 있게 보고 싶습니다.",
    "회의 준비": "팀이나 경영진과 공유할 수 있도록 핵심만 빠르게 정리해야 합니다.",
    "직접 입력": "",
}

GOAL_PRESETS = {
    "매수 판단": "지금 시점에서 매수 검토가 가능한지 판단 근거를 정리하고 싶습니다.",
    "리스크 점검": "당장 주의해서 봐야 할 리스크와 확인 포인트를 알고 싶습니다.",
    "요약 보고": "짧은 시간 안에 핵심만 파악할 수 있는 요약 보고서를 원합니다.",
    "비교 준비": "다른 종목과 비교할 수 있도록 기준점이 되는 정리를 원합니다.",
    "직접 입력": "",
}

QUESTION_PRESETS = {
    "강점과 약점": "이 종목의 강점과 약점을 균형 있게 정리해 주세요.",
    "최근 분기 해석": "최근 분기 실적이 개선 국면인지 둔화 국면인지 설명해 주세요.",
    "진입 시점 판단": "현재 시점의 진입 판단에서 가장 중요한 포인트를 짚어 주세요.",
    "10줄 요약": "회의 전에 바로 읽을 수 있게 10줄 안팎으로 요약해 주세요.",
    "직접 입력": "",
}

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
    "Total Assets": "총자산",
    "Total Liabilities Net Minority Interest": "총부채",
    "Stockholders Equity": "자본총계",
    "Operating Cash Flow": "영업활동현금흐름",
    "Investing Cash Flow": "투자활동현금흐름",
    "Financing Cash Flow": "재무활동현금흐름",
}

FINANCIAL_SECTION_LABELS = {
    "Quarterly Income Statement": "분기 손익계산서",
    "Quarterly Balance Sheet": "분기 재무상태표",
    "Quarterly Cash Flow": "분기 현금흐름표",
}


@dataclass(frozen=True)
class SearchResult:
    symbol: str
    name: str
    exchange: str = "NASDAQ"

    @property
    def label(self) -> str:
        return f"{self.symbol} | {self.name} | {self.exchange}"


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
    page_title="투자 보고서 작성 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans KR', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(219, 234, 254, 0.65), transparent 28%),
                radial-gradient(circle at top right, rgba(209, 250, 229, 0.55), transparent 22%),
                linear-gradient(180deg, #f4f7fb 0%, #eef3f8 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }

        .hero {
            padding: 1.35rem 1.5rem;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(241,245,249,0.94));
            border: 1px solid rgba(148, 163, 184, 0.24);
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.35rem;
        }

        .hero-copy {
            color: #334155;
            line-height: 1.7;
            font-size: 0.98rem;
        }

        .panel {
            padding: 1rem 1.1rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }

        .panel-title {
            font-size: 1.02rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.4rem;
        }

        .panel-copy {
            color: #475569;
            font-size: 0.93rem;
            line-height: 1.65;
        }

        .stat-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 0.85rem;
        }

        .stat-card {
            border-radius: 16px;
            padding: 0.9rem 1rem;
            background: #f8fafc;
            border: 1px solid rgba(148, 163, 184, 0.18);
        }

        .stat-label {
            color: #64748b;
            font-size: 0.78rem;
            margin-bottom: 0.2rem;
        }

        .stat-value {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.35;
        }

        .section-spacer {
            height: 0.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_state() -> None:
    defaults: dict[str, Any] = {
        "search_query": "Apple",
        "search_hits": [],
        "search_feedback": None,
        "selected_symbol": None,
        "selected_name": None,
        "selected_exchange": None,
        "basic_frame": None,
        "financial_frames": {},
        "basic_info_markdown": "",
        "financial_markdown": "",
        "status": STATUS_PRESETS["처음 보는 종목"],
        "goal": GOAL_PRESETS["매수 판단"],
        "question": QUESTION_PRESETS["강점과 약점"],
        "latest_report": None,
        "latest_report_symbol": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _select_preset(label: str, options: dict[str, str], key: str, custom_label: str) -> str:
    choice_key = f"{key}_choice"
    current_value = st.session_state.get(key, "")
    matched_choice = next((name for name, text in options.items() if text == current_value and text), custom_label)
    current_choice = st.session_state.get(choice_key, matched_choice)
    selected_choice = st.selectbox(label, list(options.keys()), index=list(options.keys()).index(current_choice))
    if selected_choice == custom_label:
        value = st.text_area(
            f"{label} 직접 입력",
            value=current_value if current_choice == custom_label else "",
            height=90,
            key=f"{key}_text",
        )
    else:
        value = options[selected_choice]
    st.session_state[choice_key] = selected_choice
    st.session_state[key] = value
    return value


def _translate_basic_frame(frame: pd.DataFrame) -> pd.DataFrame:
    translated = frame.copy()
    if len(translated.columns) >= 2:
        translated.columns = ["항목", "값"]
    if "항목" in translated.columns:
        translated["항목"] = translated["항목"].replace(BASIC_INFO_LABELS)
    return translated


def _translate_financial_frame(frame: pd.DataFrame) -> pd.DataFrame:
    translated = frame.copy()
    translated.index = [FINANCIAL_LABELS.get(str(idx), str(idx)) for idx in translated.index]
    translated.index.name = "항목"
    return translated


def _financials_to_markdown(financial_frames: dict[str, Any]) -> str:
    sections: list[str] = []
    for title, frame in financial_frames.items():
        translated = _translate_financial_frame(frame)
        label = FINANCIAL_SECTION_LABELS.get(title, title)
        sections.append(f"### {label}\n{translated.to_markdown()}")
    return "\n\n".join(sections)


def _reset_selection() -> None:
    for key, value in {
        "selected_symbol": None,
        "selected_name": None,
        "selected_exchange": None,
        "basic_frame": None,
        "financial_frames": {},
        "basic_info_markdown": "",
        "financial_markdown": "",
        "latest_report": None,
        "latest_report_symbol": None,
    }.items():
        st.session_state[key] = value


def _perform_search(query: str) -> None:
    result = stock_search(query)
    hits = [
        SearchResult(
            symbol=hit.get("symbol", "").strip(),
            name=hit.get("name", "").strip(),
            exchange=hit.get("exchange", "NASDAQ").strip(),
        )
        for hit in result.get("hits", [])
        if hit.get("symbol") and hit.get("name")
    ]
    st.session_state["search_query"] = query
    st.session_state["search_hits"] = hits
    st.session_state["search_feedback"] = result
    if not hits:
        _reset_selection()


def _load_stock_data(symbol: str, name: str, exchange: str) -> None:
    stock = Stock(symbol)
    basic_frame_raw = stock.get_basic_info_frame()
    financial_frames_raw = stock.get_financial_statement_frames()

    basic_frame = _translate_basic_frame(basic_frame_raw)
    financial_frames = {
        title: _translate_financial_frame(frame)
        for title, frame in financial_frames_raw.items()
    }

    st.session_state["selected_symbol"] = symbol
    st.session_state["selected_name"] = name
    st.session_state["selected_exchange"] = exchange
    st.session_state["basic_frame"] = basic_frame
    st.session_state["financial_frames"] = financial_frames
    st.session_state["basic_info_markdown"] = basic_frame.to_markdown(index=False)
    st.session_state["financial_markdown"] = _financials_to_markdown(financial_frames_raw)
    st.session_state["latest_report"] = None
    st.session_state["latest_report_symbol"] = None


def _feedback_message(feedback: dict[str, Any] | None) -> tuple[str, str]:
    if not feedback:
        return "info", "회사명 또는 티커를 입력한 뒤 검색을 실행하세요."

    source = feedback.get("source")
    error_type = feedback.get("error_type")
    index_name = feedback.get("index_name", "nasdaq")

    if source == "meilisearch":
        return "success", f"Meilisearch 인덱스 `{index_name}`에서 검색 결과를 불러왔습니다."
    if error_type == "index_not_found":
        return "warning", f"Meilisearch 인덱스 `{index_name}`를 찾지 못해 기본 후보 목록으로 대체했습니다."
    if source == "fallback":
        return "warning", "검색 엔진 연결이 원활하지 않아 기본 후보 목록으로 대체했습니다."
    if source == "empty":
        return "info", "검색어를 입력하면 후보 종목을 찾아드립니다."
    return "info", "검색 결과를 확인하고 종목을 선택하세요."


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">투자 보고서 작성 시스템</div>
            <div class="hero-copy">
                종목 검색, 기본 재무 데이터 확인, AI 기반 투자 보고서 생성을 하나의 화면에서 처리합니다.
                Meilisearch로 후보를 찾고, yfinance로 데이터를 읽고, OpenAI 모델로 보고서를 정리합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_overview() -> None:
    selected_name = st.session_state.get("selected_name") or "선택 전"
    selected_symbol = st.session_state.get("selected_symbol") or "-"
    feedback = st.session_state.get("search_feedback") or {}
    search_source = feedback.get("source", "대기")
    hit_count = len(st.session_state.get("search_hits", []))

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">현재 작업 상태</div>
            <div class="panel-copy">검색부터 보고서 생성까지 필요한 핵심 상태를 한눈에 확인할 수 있습니다.</div>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-label">선택 종목</div>
                    <div class="stat-value">{selected_name}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">티커</div>
                    <div class="stat-value">{selected_symbol}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">검색 결과 수</div>
                    <div class="stat-value">{hit_count}개 / {search_source}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_search_section() -> None:
    st.subheader("1. 종목 검색")
    query = st.text_input(
        "회사명 또는 티커",
        value=st.session_state.get("search_query", "Apple"),
        placeholder="예: Apple, AAPL, NVIDIA, Palantir",
    )
    search_col, clear_col = st.columns([1, 1])
    with search_col:
        if st.button("검색 실행", use_container_width=True):
            _perform_search(query)
    with clear_col:
        if st.button("선택 초기화", use_container_width=True):
            _reset_selection()

    level, message = _feedback_message(st.session_state.get("search_feedback"))
    getattr(st, level)(message)

    hits: list[SearchResult] = st.session_state.get("search_hits", [])
    if not hits:
        return

    hit_frame = pd.DataFrame(
        [{"티커": hit.symbol, "기업명": hit.name, "거래소": hit.exchange} for hit in hits]
    )
    st.dataframe(hit_frame, use_container_width=True, hide_index=True)

    labels = [hit.label for hit in hits]
    current_symbol = st.session_state.get("selected_symbol")
    default_index = next((idx for idx, hit in enumerate(hits) if hit.symbol == current_symbol), 0)
    selected_label = st.selectbox("후보 선택", labels, index=default_index)
    selected_hit = hits[labels.index(selected_label)]

    if st.button("선택 종목 데이터 불러오기", type="primary", use_container_width=True):
        try:
            with st.spinner("기본 정보와 분기 재무 데이터를 불러오는 중입니다..."):
                _load_stock_data(selected_hit.symbol, selected_hit.name, selected_hit.exchange)
            st.success(f"{selected_hit.name}({selected_hit.symbol}) 데이터를 불러왔습니다.")
        except Exception as exc:
            st.error(f"종목 데이터를 불러오는 중 오류가 발생했습니다: {exc}")


def _render_prompt_section() -> None:
    st.subheader("2. 보고서 목적 설정")
    left, right = st.columns(2)
    with left:
        _select_preset("현재 검토 상황", STATUS_PRESETS, "status", "직접 입력")
        _select_preset("보고서 목표", GOAL_PRESETS, "goal", "직접 입력")
    with right:
        _select_preset("중점 질문", QUESTION_PRESETS, "question", "직접 입력")
        st.text_area(
            "사용할 데이터 범위 메모",
            value="최근 분기 재무 흐름과 기본 기업 정보를 바탕으로 정리",
            height=90,
            disabled=True,
            help="현재 버전에서는 yfinance 기반 기본 정보와 최근 분기 재무 데이터를 사용합니다.",
        )


def _render_data_section() -> None:
    basic_frame: pd.DataFrame | None = st.session_state.get("basic_frame")
    financial_frames: dict[str, pd.DataFrame] = st.session_state.get("financial_frames") or {}

    st.subheader("3. 데이터 검토")
    if basic_frame is None:
        st.info("검색 결과에서 종목을 선택하고 데이터를 먼저 불러와 주세요.")
        return

    selected_name = st.session_state.get("selected_name")
    selected_symbol = st.session_state.get("selected_symbol")
    selected_exchange = st.session_state.get("selected_exchange")
    st.caption(f"{selected_name} ({selected_symbol}) · {selected_exchange}")

    basic_col, financial_col = st.columns([1, 1.25])
    with basic_col:
        st.markdown("**기본 정보**")
        st.dataframe(basic_frame, use_container_width=True, hide_index=True)

    with financial_col:
        st.markdown("**분기 재무 데이터**")
        for title, frame in financial_frames.items():
            st.markdown(f"**{title}**")
            st.dataframe(frame, use_container_width=True)


def _render_report_section() -> None:
    st.subheader("4. 투자 보고서 생성")
    selected_symbol = st.session_state.get("selected_symbol")
    selected_name = st.session_state.get("selected_name")

    if not selected_symbol:
        st.info("먼저 종목을 선택하고 데이터를 불러와 주세요.")
        return

    generate_col, reset_col = st.columns([1, 1])
    with generate_col:
        if st.button("AI 투자 보고서 생성", type="primary", use_container_width=True):
            try:
                with st.spinner("투자 보고서를 생성하는 중입니다..."):
                    report = investment_report(
                        company=selected_name,
                        symbol=selected_symbol,
                        basic_info=st.session_state["basic_info_markdown"],
                        financials=st.session_state["financial_markdown"],
                        status=st.session_state["status"],
                        goal=st.session_state["goal"],
                        question=st.session_state["question"],
                    )
                st.session_state["latest_report"] = report
                st.session_state["latest_report_symbol"] = selected_symbol
                st.success("보고서 생성을 완료했습니다.")
            except Exception as exc:
                st.error(f"보고서 생성 중 오류가 발생했습니다: {exc}")

    with reset_col:
        if st.button("보고서만 초기화", use_container_width=True):
            st.session_state["latest_report"] = None
            st.session_state["latest_report_symbol"] = None

    report = st.session_state.get("latest_report")
    if report:
        st.markdown(report)
        st.download_button(
            "보고서 다운로드 (.md)",
            data=report.encode("utf-8"),
            file_name=f"investment_report_{st.session_state.get('latest_report_symbol', 'report')}.md",
            mime="text/markdown",
            use_container_width=True,
        )


def main() -> None:
    _apply_theme()
    _init_state()
    _render_header()
    _render_overview()

    left, right = st.columns([1, 1.25], gap="large")
    with left:
        _render_search_section()
        st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)
        _render_prompt_section()
    with right:
        _render_data_section()
        st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)
        _render_report_section()


if __name__ == "__main__":
    main()
