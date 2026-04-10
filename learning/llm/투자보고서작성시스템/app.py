from __future__ import annotations

import re
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
    "Quarterly Income Statement": "손익계산서",
    "Quarterly Balance Sheet": "재무상태표",
    "Quarterly Cash Flow": "현금흐름표",
}

STEP_META = [
    ("search", "종목 검색"),
    ("setup", "분석 설정"),
    ("review", "데이터 검토"),
    ("report", "보고서 생성"),
]


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
                radial-gradient(circle at top left, rgba(219, 234, 254, 0.55), transparent 24%),
                radial-gradient(circle at top right, rgba(226, 232, 240, 0.72), transparent 28%),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: rgba(248, 250, 252, 0.96);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }

        .block-container {
            max-width: 1220px;
            padding-top: 1.05rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.02em;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.05rem;
        }

        .hero-shell {
            padding: 1.35rem 1.45rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(248,250,252,0.95));
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.05);
            margin-bottom: 0.9rem;
        }

        .hero-kicker {
            color: #2563eb;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }

        .hero-title {
            color: #0f172a;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .hero-copy {
            color: #475569;
            font-size: 0.98rem;
            line-height: 1.7;
        }

        .page-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.2rem;
        }

        .page-copy {
            color: #475569;
            line-height: 1.65;
            font-size: 0.95rem;
            margin-bottom: 0.95rem;
        }

        .soft-note {
            color: #64748b;
            font-size: 0.88rem;
            line-height: 1.55;
        }

        .report-shell {
            background: rgba(255,255,255,0.95);
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 20px;
            padding: 1.1rem 1.2rem;
        }

        .report-shell h1 {
            font-size: 1.55rem;
            margin-top: 0.1rem;
            margin-bottom: 0.8rem;
            color: #0f172a;
        }

        .report-shell h2 {
            font-size: 1.08rem;
            margin-top: 1.1rem;
            margin-bottom: 0.45rem;
            color: #111827;
        }

        .report-shell h3 {
            font-size: 0.98rem;
            margin-top: 0.9rem;
            margin-bottom: 0.35rem;
            color: #1f2937;
        }

        .report-shell p, .report-shell li {
            color: #1f2937;
            line-height: 1.8;
            font-size: 0.96rem;
        }

        .report-shell ul, .report-shell ol {
            padding-left: 1.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_state() -> None:
    defaults: dict[str, Any] = {
        "step": "search",
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
        "status_choice": "처음 보는 종목",
        "goal": GOAL_PRESETS["매수 판단"],
        "goal_choice": "매수 판단",
        "question": QUESTION_PRESETS["강점과 약점"],
        "question_choice": "강점과 약점",
        "latest_report": None,
        "latest_report_symbol": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _step_index(step: str | None = None) -> int:
    current = step or st.session_state.get("step", "search")
    return [key for key, _ in STEP_META].index(current)


def _go_to(step: str) -> None:
    st.session_state["step"] = step


def _go_next() -> None:
    idx = _step_index()
    if idx < len(STEP_META) - 1:
        st.session_state["step"] = STEP_META[idx + 1][0]


def _go_prev() -> None:
    idx = _step_index()
    if idx > 0:
        st.session_state["step"] = STEP_META[idx - 1][0]


def _selected_ready() -> bool:
    return bool(st.session_state.get("selected_symbol"))


def _select_preset(label: str, options: dict[str, str], key: str) -> str:
    option_names = list(options.keys())
    choice_key = f"{key}_choice"
    current_choice = st.session_state.get(choice_key, option_names[0])
    if current_choice not in option_names:
        current_choice = option_names[0]

    selected_choice = st.selectbox(
        label,
        option_names,
        index=option_names.index(current_choice),
        key=f"widget_{choice_key}",
    )

    if selected_choice == "직접 입력":
        value = st.text_area(
            f"{label} 직접 입력",
            value=st.session_state.get(key, ""),
            height=100,
            key=f"widget_{key}_text",
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


def _clean_report(report: str) -> str:
    cleaned = (report or "").strip()
    cleaned = re.sub(r"^```(?:markdown|md)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


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
        <div class="hero-shell">
            <div class="hero-kicker">Investment Workflow</div>
            <div class="hero-title">투자 보고서 작성 시스템</div>
            <div class="hero-copy">
                종목 검색, 분석 목적 설정, 데이터 검토, 보고서 생성까지 필요한 흐름을 단계별로 분리했습니다.
                한 번에 모든 것을 보여주기보다 현재 단계에 집중할 수 있게 구성한 화면입니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_progress() -> None:
    current_idx = _step_index()
    cols = st.columns(4)
    for idx, (_, label) in enumerate(STEP_META):
        status = "대기"
        delta = None
        if idx < current_idx:
            status = "완료"
        elif idx == current_idx:
            status = "진행 중"
            delta = "현재 단계"
        with cols[idx]:
            with st.container(border=True):
                st.caption(f"STEP {idx + 1}")
                st.markdown(f"**{label}**")
                st.metric("상태", status, delta=delta, label_visibility="collapsed")


def _render_summary() -> None:
    selected_name = st.session_state.get("selected_name") or "선택 전"
    selected_symbol = st.session_state.get("selected_symbol") or "-"
    hit_count = len(st.session_state.get("search_hits", []))
    report_status = "완료" if st.session_state.get("latest_report") else "대기"
    feedback = st.session_state.get("search_feedback") or {}
    search_source = feedback.get("source", "대기")

    cols = st.columns(4)
    items = [
        ("선택 종목", selected_name),
        ("티커", selected_symbol),
        ("검색 결과", f"{hit_count}개 / {search_source}"),
        ("보고서 상태", report_status),
    ]
    for col, (label, value) in zip(cols, items):
        with col:
            with st.container(border=True):
                st.caption(label)
                st.markdown(f"**{value}**")


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 진행 단계")
        for key, label in STEP_META:
            button_type = "primary" if st.session_state.get("step") == key else "secondary"
            if st.button(f"{_step_index(key) + 1}. {label}", key=f"nav_{key}", use_container_width=True, type=button_type):
                _go_to(key)

        st.markdown("---")
        st.markdown("### 현재 선택")
        st.write(f"**종목**: {st.session_state.get('selected_name') or '선택 전'}")
        st.write(f"**티커**: {st.session_state.get('selected_symbol') or '-'}")
        st.write(f"**거래소**: {st.session_state.get('selected_exchange') or '-'}")

        st.markdown("---")
        if st.button("전체 초기화", use_container_width=True):
            keep = {
                "search_query": "Apple",
                "status": STATUS_PRESETS["처음 보는 종목"],
                "status_choice": "처음 보는 종목",
                "goal": GOAL_PRESETS["매수 판단"],
                "goal_choice": "매수 판단",
                "question": QUESTION_PRESETS["강점과 약점"],
                "question_choice": "강점과 약점",
                "step": "search",
            }
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            for key, value in keep.items():
                st.session_state[key] = value
            st.rerun()


def _page_heading(title: str, copy: str) -> None:
    st.markdown(f"<div class='page-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='page-copy'>{copy}</div>", unsafe_allow_html=True)


def _render_search_page() -> None:
    _page_heading(
        "종목 검색",
        "회사명이나 티커를 입력해 후보를 찾고, 검토할 종목을 선택합니다.",
    )

    with st.container(border=True):
        query = st.text_input(
            "회사명 또는 티커",
            value=st.session_state.get("search_query", "Apple"),
            placeholder="예: Apple, AAPL, NVIDIA, Palantir",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("검색 실행", use_container_width=True, type="primary"):
                _perform_search(query)
        with c2:
            if st.button("선택 초기화", use_container_width=True):
                _reset_selection()

        level, message = _feedback_message(st.session_state.get("search_feedback"))
        getattr(st, level)(message)

    hits: list[SearchResult] = st.session_state.get("search_hits", [])
    if hits:
        with st.container(border=True):
            st.markdown("#### 검색 결과")
            hit_frame = pd.DataFrame(
                [{"티커": hit.symbol, "기업명": hit.name, "거래소": hit.exchange} for hit in hits]
            )
            st.dataframe(hit_frame, use_container_width=True, hide_index=True)

            labels = [hit.label for hit in hits]
            current_symbol = st.session_state.get("selected_symbol")
            default_index = next((idx for idx, hit in enumerate(hits) if hit.symbol == current_symbol), 0)
            selected_label = st.selectbox("후보 선택", labels, index=default_index)
            selected_hit = hits[labels.index(selected_label)]

            if st.button("이 종목으로 진행", use_container_width=True, type="primary"):
                try:
                    with st.spinner("기본 정보와 분기 재무 데이터를 불러오는 중입니다..."):
                        _load_stock_data(selected_hit.symbol, selected_hit.name, selected_hit.exchange)
                    st.success(f"{selected_hit.name} ({selected_hit.symbol}) 데이터를 불러왔습니다.")
                    _go_to("setup")
                    st.rerun()
                except Exception as exc:
                    st.error(f"종목 데이터를 불러오는 중 오류가 발생했습니다: {exc}")

    _render_step_footer(show_prev=False, next_label="다음 단계", next_disabled=not _selected_ready())


def _render_setup_page() -> None:
    _page_heading(
        "분석 설정",
        "현재 검토 상황, 보고서 목표, 중점 질문을 설정합니다. 직접 입력으로 목적을 세밀하게 조정할 수도 있습니다.",
    )

    if not _selected_ready():
        st.warning("먼저 종목을 선택해 주세요.")
        _render_step_footer(show_prev=True, next_label="다음 단계", next_disabled=True)
        return

    with st.container(border=True):
        left, right = st.columns(2)
        with left:
            _select_preset("현재 검토 상황", STATUS_PRESETS, "status")
            _select_preset("보고서 목표", GOAL_PRESETS, "goal")
        with right:
            _select_preset("중점 질문", QUESTION_PRESETS, "question")
            st.text_area(
                "사용 데이터 범위",
                value="최근 분기 재무 흐름과 기본 기업 정보를 기준으로 정리",
                height=100,
                disabled=True,
            )

    _render_step_footer(show_prev=True, next_label="다음 단계", next_disabled=False)


def _render_review_page() -> None:
    _page_heading(
        "데이터 검토",
        "기본 정보와 최근 분기 재무 데이터를 먼저 확인한 뒤, 보고서 생성 여부를 결정합니다.",
    )

    basic_frame: pd.DataFrame | None = st.session_state.get("basic_frame")
    financial_frames: dict[str, pd.DataFrame] = st.session_state.get("financial_frames") or {}

    if basic_frame is None:
        st.warning("먼저 검색 단계에서 종목 데이터를 불러와 주세요.")
        _render_step_footer(show_prev=True, next_label="다음 단계", next_disabled=True)
        return

    st.caption(
        f"{st.session_state.get('selected_name')} ({st.session_state.get('selected_symbol')}) · {st.session_state.get('selected_exchange')}"
    )

    tabs = st.tabs(["기본 정보", "손익계산서", "재무상태표", "현금흐름표"])
    with tabs[0]:
        st.dataframe(basic_frame, use_container_width=True, hide_index=True)

    section_lookup = {
        "손익계산서": "Quarterly Income Statement",
        "재무상태표": "Quarterly Balance Sheet",
        "현금흐름표": "Quarterly Cash Flow",
    }
    for tab, section_name in zip(tabs[1:], list(section_lookup.keys())):
        with tab:
            frame = financial_frames.get(section_lookup[section_name])
            if frame is None or frame.empty:
                st.info("데이터가 없습니다.")
            else:
                st.dataframe(frame, use_container_width=True)

    st.markdown(
        "<div class='soft-note'>원천 데이터 제공 범위에 따라 일부 항목이 비어 있거나 표시되지 않을 수 있습니다.</div>",
        unsafe_allow_html=True,
    )

    _render_step_footer(show_prev=True, next_label="다음 단계", next_disabled=False)


def _render_report_page() -> None:
    _page_heading(
        "보고서 생성",
        "설정한 목적과 질문을 기준으로 AI 투자 보고서를 생성합니다. 결과는 화면에서 읽거나 마크다운 파일로 저장할 수 있습니다.",
    )

    if not _selected_ready():
        st.warning("먼저 종목을 선택하고 데이터를 불러와 주세요.")
        _render_step_footer(show_prev=True, show_next=False)
        return

    c1, c2 = st.columns(2)
    with c1:
        if st.button("AI 투자 보고서 생성", type="primary", use_container_width=True):
            try:
                with st.spinner("투자 보고서를 생성하는 중입니다..."):
                    report = investment_report(
                        company=st.session_state["selected_name"],
                        symbol=st.session_state["selected_symbol"],
                        basic_info=st.session_state["basic_info_markdown"],
                        financials=st.session_state["financial_markdown"],
                        status=st.session_state["status"],
                        goal=st.session_state["goal"],
                        question=st.session_state["question"],
                    )
                cleaned = _clean_report(report)
                st.session_state["latest_report"] = cleaned
                st.session_state["latest_report_symbol"] = st.session_state["selected_symbol"]
                st.success("보고서 생성을 완료했습니다.")
            except Exception as exc:
                st.error(f"보고서 생성 중 오류가 발생했습니다: {exc}")
    with c2:
        if st.button("보고서 초기화", use_container_width=True):
            st.session_state["latest_report"] = None
            st.session_state["latest_report_symbol"] = None
            st.rerun()

    report = st.session_state.get("latest_report")
    if report:
        st.markdown("<div class='report-shell'>", unsafe_allow_html=True)
        st.markdown(report)
        st.markdown("</div>", unsafe_allow_html=True)
        st.download_button(
            "보고서 다운로드 (.md)",
            data=report.encode("utf-8"),
            file_name=f"investment_report_{st.session_state.get('latest_report_symbol', 'report')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        st.info("아직 생성된 보고서가 없습니다.")

    _render_step_footer(show_prev=True, show_next=False)


def _render_step_footer(
    *,
    show_prev: bool = True,
    show_next: bool = True,
    next_label: str = "다음 단계",
    next_disabled: bool = False,
) -> None:
    st.write("")
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if show_prev and st.button("이전", use_container_width=True, key=f"prev_{st.session_state.get('step')}"):
            _go_prev()
            st.rerun()
    with cols[1]:
        if show_next and st.button(
            next_label,
            use_container_width=True,
            disabled=next_disabled,
            key=f"next_{st.session_state.get('step')}",
        ):
            _go_next()
            st.rerun()


def main() -> None:
    _apply_theme()
    _init_state()
    _render_sidebar()
    _render_header()
    _render_progress()
    _render_summary()
    st.write("")

    step = st.session_state.get("step", "search")
    if step == "search":
        _render_search_page()
    elif step == "setup":
        _render_setup_page()
    elif step == "review":
        _render_review_page()
    elif step == "report":
        _render_report_page()


if __name__ == "__main__":
    main()
