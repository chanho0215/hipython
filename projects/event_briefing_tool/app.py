from __future__ import annotations

from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from event_weekly_briefing_service_v4 import (
    CACHE_PATH,
    DART_API_KEY,
    DEFAULT_COMPANY_INDEX,
    DEFAULT_MEILI_URL,
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
    CompanyHit,
    EventItem,
    fetch_company_events_for_month_week,
    fetch_company_overview,
    generate_weekly_briefing_structured,
    month_week_date_range,
    search_companies,
    valid_weeks_for_month,
    week_label,
    weekly_briefing_to_markdown,
)

STEP_META = [("search", "회사 선택"), ("week", "주차 선택"), ("briefing", "브리핑")]

OVERVIEW_LABELS = {
    "corp_name": "회사명",
    "stock_name": "종목명",
    "stock_code": "종목코드",
    "ceo_nm": "대표자",
    "corp_cls": "시장구분",
    "hm_url": "홈페이지",
    "ir_url": "IR 홈페이지",
    "est_dt": "설립일",
    "acc_mt": "결산월",
}


def _load_env() -> None:
    current = Path(__file__).resolve()
    for candidate in (current.parent / ".env", current.parent.parent / ".env", current.parent.parent.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)


_load_env()

st.set_page_config(page_title="주간 공시·뉴스 브리핑", page_icon="🗓️", layout="wide", initial_sidebar_state="expanded")


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'IBM Plex Sans KR', sans-serif; }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(219, 234, 254, 0.40), transparent 24%),
                radial-gradient(circle at top right, rgba(220, 252, 231, 0.36), transparent 24%),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: rgba(248,250,252,0.98);
            border-right: 1px solid rgba(148,163,184,0.16);
        }
        .block-container { max-width: 1160px; padding-top: 1rem; padding-bottom: 2rem; }
        .hero {
            padding: 1.15rem 1.25rem; border-radius: 20px; background: rgba(255,255,255,0.96);
            border: 1px solid rgba(148,163,184,0.16); box-shadow: 0 10px 24px rgba(15,23,42,0.04);
            margin-bottom: 0.9rem;
        }
        .hero-title { color: #0f172a; font-size: 1.7rem; font-weight: 700; }
        .hero-sub { color: #475569; font-size: 0.95rem; margin-top: 0.25rem; }
        .step-pill {
            padding: 0.85rem 0.95rem; border-radius: 16px; background: rgba(255,255,255,0.96);
            border: 1px solid rgba(148,163,184,0.16); min-height: 78px;
        }
        .step-pill.active { border-color: rgba(59,130,246,0.35); background: rgba(239,246,255,0.96); }
        .step-no { color: #64748b; font-size: 0.74rem; font-weight: 700; margin-bottom: 0.2rem; }
        .step-title { color: #0f172a; font-size: 0.98rem; font-weight: 700; }
        .step-state { color: #64748b; font-size: 0.84rem; margin-top: 0.2rem; }
        .summary-card {
            padding: 0.9rem 1rem; border-radius: 16px; background: rgba(255,255,255,0.96);
            border: 1px solid rgba(148,163,184,0.14); min-height: 84px;
        }
        .summary-label { color: #64748b; font-size: 0.78rem; margin-bottom: 0.22rem; }
        .summary-value { color: #0f172a; font-size: 1rem; font-weight: 700; line-height: 1.35; }
        .event-card {
            padding: 0.9rem 1rem; border-radius: 16px; background: rgba(255,255,255,0.98);
            border: 1px solid rgba(148,163,184,0.16); margin-bottom: 0.75rem;
        }
        .event-meta { color: #64748b; font-size: 0.79rem; margin-bottom: 0.25rem; }
        .event-title { color: #111827; font-weight: 700; margin-bottom: 0.35rem; }
        .event-copy { color: #334155; font-size: 0.93rem; line-height: 1.62; }
        .brief-hero {
            padding: 1rem 1.1rem; border-radius: 18px;
            background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
            border: 1px solid rgba(96,165,250,0.22); box-shadow: 0 10px 24px rgba(37,99,235,0.06);
        }
        .brief-title { color: #0f172a; font-size: 1.35rem; font-weight: 700; margin-bottom: 0.28rem; }
        .brief-summary { color: #1e3a8a; font-size: 0.96rem; line-height: 1.65; }
        .brief-card {
            min-height: 220px; height: 220px; padding: 0.95rem 1rem; border-radius: 16px;
            background: rgba(255,255,255,0.98); border: 1px solid rgba(148,163,184,0.16);
            box-shadow: 0 8px 18px rgba(15,23,42,0.04); overflow: auto; margin-bottom: 1rem;
        }
        .brief-card h4 { margin: 0 0 0.6rem 0; color: #111827; font-size: 1rem; }
        .brief-card ul { margin: 0; padding-left: 1.1rem; }
        .brief-card li { color: #334155; line-height: 1.68; margin-bottom: 0.45rem; font-size: 0.94rem; }
        .split-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.9rem; }
        .split-col-title { color: #64748b; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.3rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_state() -> None:
    defaults: dict[str, Any] = {
        "step": "search",
        "company_query": "삼성전자",
        "company_hits": [],
        "company_feedback": None,
        "selected_company": None,
        "company_overview": None,
        "selected_year": 2026,
        "selected_month": 3,
        "selected_week_no": 1,
        "weekly_bundle": {"all": [], "disclosures": [], "news": [], "news_debug": {}},
        "latest_weekly_briefing": None,
        "latest_weekly_markdown": None,
        "disclosure_limit": 40,
        "news_limit": 30,
        "week_load_attempted": False,
        "loaded_period_key": None,
        "generated_period_key": None,
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


def _selected_company() -> CompanyHit | None:
    raw = st.session_state.get("selected_company")
    return CompanyHit(**raw) if raw else None


def _weekly_bundle() -> dict[str, Any]:
    return st.session_state.get("weekly_bundle", {}) or {}


def _period_key(year: int, month: int, week_no: int) -> tuple[int, int, int]:
    return (int(year), int(month), int(week_no))


def _current_period_key() -> tuple[int, int, int]:
    return _period_key(st.session_state["selected_year"], st.session_state["selected_month"], st.session_state["selected_week_no"])


def _reset_company_dependent_state() -> None:
    st.session_state["company_overview"] = None
    st.session_state["weekly_bundle"] = {"all": [], "disclosures": [], "news": [], "news_debug": {}}
    st.session_state["latest_weekly_briefing"] = None
    st.session_state["latest_weekly_markdown"] = None
    st.session_state["generated_period_key"] = None
    st.session_state["week_load_attempted"] = False
    st.session_state["loaded_period_key"] = None
    st.session_state["generated_period_key"] = None


def _perform_company_search() -> None:
    result = search_companies(st.session_state.get("company_query", ""))
    st.session_state["company_hits"] = [CompanyHit(**hit) for hit in result.get("hits", [])]
    st.session_state["company_feedback"] = result


def _select_company(hit: CompanyHit) -> None:
    st.session_state["selected_company"] = asdict(hit)
    _reset_company_dependent_state()


def _load_weekly_events() -> None:
    company = _selected_company()
    if not company:
        raise RuntimeError("회사를 먼저 선택해 주세요.")
    year, month, week_no = _current_period_key()
    bundle = fetch_company_events_for_month_week(
        corp_code=company.corp_code,
        company_name=company.corp_name,
        stock_code=company.stock_code,
        year=year,
        month=month,
        week_no=week_no,
        disclosure_limit=int(st.session_state.get("disclosure_limit", 40)),
        news_limit=int(st.session_state.get("news_limit", 30)),
    )
    st.session_state["weekly_bundle"] = bundle
    st.session_state["week_load_attempted"] = True
    st.session_state["loaded_period_key"] = _current_period_key()
    try:
        st.session_state["company_overview"] = fetch_company_overview(company.corp_code)
    except Exception:
        st.session_state["company_overview"] = None
    st.session_state["latest_weekly_briefing"] = None
    st.session_state["latest_weekly_markdown"] = None


def _generate_weekly_briefing() -> None:
    company = _selected_company()
    bundle = _weekly_bundle()
    if not company:
        raise RuntimeError("회사를 먼저 선택해 주세요.")
    if not bundle.get("all"):
        raise RuntimeError("먼저 주간 이벤트를 불러와 주세요.")
    briefing = generate_weekly_briefing_structured(
        company_name=company.corp_name,
        stock_code=company.stock_code,
        week_label=bundle.get("week_label", week_label(*_current_period_key())),
        overview=st.session_state.get("company_overview"),
        disclosures=bundle.get("disclosures", []),
        news=bundle.get("news", []),
        all_events=bundle.get("all", []),
    )
    st.session_state["latest_weekly_briefing"] = briefing
    st.session_state["latest_weekly_markdown"] = weekly_briefing_to_markdown(briefing)
    st.session_state["generated_period_key"] = _current_period_key()


def _feedback_message() -> tuple[str, str]:
    feedback = st.session_state.get("company_feedback") or {}
    if not feedback:
        return "info", "회사명 또는 종목코드를 검색하세요."
    source = feedback.get("source")
    if source == "meilisearch":
        return "success", "회사 검색 결과를 불러왔습니다."
    if source == "cache":
        return "warning", "검색 인덱스 대신 로컬 캐시로 검색했습니다."
    if source == "unavailable":
        return "warning", "회사 검색 인덱스를 찾지 못했습니다."
    return "info", feedback.get("message", "검색 결과를 확인해 주세요.")


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">주간 공시·뉴스 브리핑</div>
            <div class="hero-sub">회사 선택 → 주차 선택 → 브리핑</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_progress() -> None:
    current_idx = _step_index()
    cols = st.columns(len(STEP_META))
    for idx, (_, label) in enumerate(STEP_META):
        active = " active" if idx == current_idx else ""
        state = "완료" if idx < current_idx else "진행 중" if idx == current_idx else "대기"
        with cols[idx]:
            st.markdown(
                f"""
                <div class="step-pill{active}">
                    <div class="step-no">STEP {idx + 1}</div>
                    <div class="step-title">{escape(label)}</div>
                    <div class="step-state">{escape(state)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_summary() -> None:
    company = _selected_company()
    bundle = _weekly_bundle()
    label = bundle.get("week_label") or week_label(*_current_period_key())
    cards = [
        ("회사", company.corp_name if company else "선택 전"),
        ("주차", label),
        ("공시", f"{len(bundle.get('disclosures', []))}건"),
        ("뉴스", f"{len(bundle.get('news', []))}건"),
    ]
    cols = st.columns(4)
    for col, (label_text, value) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="summary-label">{escape(label_text)}</div>
                    <div class="summary-value">{escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 진행")
        for idx, (key, label) in enumerate(STEP_META, start=1):
            kind = "primary" if st.session_state.get("step") == key else "secondary"
            if st.button(f"{idx}. {label}", key=f"nav_{key}", type=kind, use_container_width=True):
                _go_to(key)
                st.rerun()
        st.markdown("---")
        company = _selected_company()
        st.markdown("### 현재 선택")
        st.write(f"**회사**: {company.corp_name if company else '선택 전'}")
        st.write(f"**주차**: {week_label(*_current_period_key())}")
        st.markdown("---")
        st.caption(f"Meilisearch: {DEFAULT_MEILI_URL}")
        st.caption(f"회사 인덱스: {DEFAULT_COMPANY_INDEX}")
        st.caption(f"DART: {'설정됨' if DART_API_KEY else '없음'}")
        st.caption(f"뉴스 API: {'설정됨' if (NAVER_CLIENT_ID and NAVER_CLIENT_SECRET) else '없음'}")
        st.markdown("---")
        if st.button("전체 초기화", use_container_width=True):
            for key in [
                "company_hits", "company_feedback", "selected_company", "company_overview",
                "latest_weekly_briefing", "latest_weekly_markdown"
            ]:
                st.session_state[key] = None if key in {"company_feedback", "selected_company", "company_overview", "latest_weekly_briefing", "latest_weekly_markdown"} else []
            st.session_state["weekly_bundle"] = {"all": [], "disclosures": [], "news": [], "news_debug": {}}
            st.session_state["week_load_attempted"] = False
            st.session_state["loaded_period_key"] = None
            st.session_state["generated_period_key"] = None
            st.session_state["step"] = "search"
            st.rerun()


def _event_card(item: EventItem) -> str:
    return (
        '<div class="event-card">'
        f'<div class="event-meta">{escape(item.source)} · {escape(item.category)} · {escape(item.occurred_at)}</div>'
        f'<div class="event-title">{escape(item.title)}</div>'
        f'<div class="event-copy">{escape(item.snippet or "요약 없음")}</div>'
        '</div>'
    )


def _render_company_search_page() -> None:
    st.subheader("1. 회사 선택")
    with st.form("company_search_form", clear_on_submit=False):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text_input("회사명 또는 종목코드", key="company_query", placeholder="예: 삼성전자, 카카오, 005930")
        with col2:
            st.write("")
            submitted = st.form_submit_button("검색", type="primary", use_container_width=True)
        if submitted:
            _perform_company_search()

    level, message = _feedback_message()
    getattr(st, level)(message)

    hits: list[CompanyHit] = st.session_state.get("company_hits", [])
    if not hits:
        return

    labels = [hit.label for hit in hits]
    default_index = 0
    current_company = _selected_company()
    if current_company:
        for i, hit in enumerate(hits):
            if hit.corp_code == current_company.corp_code:
                default_index = i
                break

    selected_label = st.radio("검색 결과", labels, index=default_index, label_visibility="collapsed")
    selected_hit = hits[labels.index(selected_label)]

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("이 회사로 계속하기", type="primary", use_container_width=True):
            _select_company(selected_hit)
            _go_next()
            st.rerun()
    with c2:
        if st.button("선택 저장", use_container_width=True):
            _select_company(selected_hit)
            st.success("선택했습니다.")


def _render_company_overview() -> None:
    overview = st.session_state.get("company_overview") or {}
    if not overview:
        return
    rows = []
    for key, label in OVERVIEW_LABELS.items():
        value = str(overview.get(key, "")).strip()
        if value:
            rows.append({"항목": label, "값": value})
    if rows:
        with st.expander("회사 정보", expanded=False):
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_news_debug() -> None:
    debug = _weekly_bundle().get("news_debug", {}) or {}
    if not debug or debug.get("total_unique", 0) > 0:
        return
    if not (NAVER_CLIENT_ID and NAVER_CLIENT_SECRET):
        return
    with st.expander("뉴스 검색 확인", expanded=False):
        attempts = debug.get("attempts", [])
        if attempts:
            frame = pd.DataFrame(
                [{"검색어": row.get("query", ""), "시작": row.get("start", 1), "API total": row.get("total", 0), "추가": row.get("added", 0), "가장오래된기사": row.get("oldest", ""), "오류": row.get("error", "")} for row in attempts]
            )
            st.dataframe(frame, use_container_width=True, hide_index=True)


def _render_week_selector_page() -> None:
    st.subheader("2. 주차 선택")
    company = _selected_company()
    if not company:
        st.info("먼저 회사를 선택하세요.")
        return

    st.write(f"**{company.corp_name} ({company.stock_code or '비상장'})**")

    year = int(st.session_state["selected_year"])
    month = int(st.session_state["selected_month"])
    valid_weeks = valid_weeks_for_month(year, month)
    if st.session_state.get("selected_week_no") not in valid_weeks:
        st.session_state["selected_week_no"] = valid_weeks[-1]

    with st.form("week_select_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            year = st.number_input("연도", min_value=2020, max_value=2035, value=int(st.session_state["selected_year"]))
        with c2:
            month = st.selectbox("월", list(range(1, 13)), index=list(range(1, 13)).index(int(st.session_state["selected_month"])))
        valid_weeks = valid_weeks_for_month(int(year), int(month))
        current_week = st.session_state.get("selected_week_no", 1)
        if current_week not in valid_weeks:
            current_week = valid_weeks[-1]
        with c3:
            week_no = st.selectbox("주차", valid_weeks, format_func=lambda x: f"{x}주차", index=valid_weeks.index(current_week))

        with st.expander("고급 옵션", expanded=False):
            o1, o2 = st.columns(2)
            with o1:
                disclosure_limit = st.number_input("공시 최대 건수", min_value=10, max_value=100, value=int(st.session_state["disclosure_limit"]))
            with o2:
                news_limit = st.number_input("뉴스 최대 건수", min_value=5, max_value=100, value=int(st.session_state["news_limit"]))

        submitted = st.form_submit_button("이 주차 이벤트 불러오기", type="primary", use_container_width=True)
        if submitted:
            st.session_state["selected_year"] = int(year)
            st.session_state["selected_month"] = int(month)
            st.session_state["selected_week_no"] = int(week_no)
            st.session_state["disclosure_limit"] = int(disclosure_limit)
            st.session_state["news_limit"] = int(news_limit)
            try:
                with st.spinner("주간 이벤트를 불러오는 중입니다..."):
                    _load_weekly_events()
                st.success("불러왔습니다.")
            except Exception as exc:
                st.error(f"이벤트 수집 중 오류가 발생했습니다: {exc}")

    current_key = _current_period_key()
    loaded_key = st.session_state.get("loaded_period_key")
    bundle = _weekly_bundle()
    if loaded_key and loaded_key != current_key and bundle.get("all"):
        st.info("선택이 바뀌었습니다. 새 주차로 다시 불러오세요.")

    if st.session_state.get("week_load_attempted") and loaded_key == current_key and not bundle.get("all"):
        st.info("이 주차에는 수집된 이벤트가 없습니다.")
        _render_news_debug()

    if loaded_key != current_key or not bundle.get("all"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← 회사 선택", use_container_width=True):
                _go_prev()
                st.rerun()
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("전체 이벤트", len(bundle.get("all", [])))
    m2.metric("공시", len(bundle.get("disclosures", [])))
    m3.metric("뉴스", len(bundle.get("news", [])))

    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("← 회사 선택", use_container_width=True, key="week_prev_top"):
            _go_prev()
            st.rerun()
    with nav2:
        if st.button("브리핑 생성", type="primary", use_container_width=True, key="week_next_top"):
            try:
                with st.spinner("주간 브리핑을 생성하는 중입니다..."):
                    _generate_weekly_briefing()
                _go_next()
                st.rerun()
            except Exception as exc:
                st.error(f"브리핑 생성 중 오류가 발생했습니다: {exc}")

    tab1, tab2, tab3 = st.tabs(["전체", "공시", "뉴스"])
    for tab, items in zip([tab1, tab2, tab3], [bundle.get("all", []), bundle.get("disclosures", []), bundle.get("news", [])]):
        with tab:
            if items:
                for item in items:
                    st.markdown(_event_card(item), unsafe_allow_html=True)
            else:
                st.info("표시할 항목이 없습니다.")

    _render_news_debug()
    _render_company_overview()


def _bullet_list_html(items: list[str], empty_message: str = "해당 사항 없음") -> str:
    values = items or [empty_message]
    return "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in values) + "</ul>"


def _single_brief_card(title: str, items: list[str]) -> str:
    return f'<div class="brief-card"><h4>{escape(title)}</h4>{_bullet_list_html(items)}</div>'


def _split_brief_card(title: str, left_title: str, left_items: list[str], right_title: str, right_items: list[str]) -> str:
    return (
        '<div class="brief-card">'
        f'<h4>{escape(title)}</h4>'
        '<div class="split-grid">'
        f'<div><div class="split-col-title">{escape(left_title)}</div>{_bullet_list_html(left_items)}</div>'
        f'<div><div class="split-col-title">{escape(right_title)}</div>{_bullet_list_html(right_items)}</div>'
        '</div>'
        '</div>'
    )


def _render_weekly_briefing_cards(briefing: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="brief-hero">
            <div class="brief-title">{escape(str(briefing.get('title', '주간 브리핑')))}</div>
            <div class="brief-summary">{escape(str(briefing.get('week_label', '')))} · {escape(str(briefing.get('one_line_summary', '')))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(_single_brief_card("핵심 이슈 TOP 3", briefing.get("top_themes", [])), unsafe_allow_html=True)
    with c2:
        st.markdown(_single_brief_card("공시 하이라이트", briefing.get("disclosure_highlights", [])), unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(_single_brief_card("뉴스 하이라이트", briefing.get("news_highlights", [])), unsafe_allow_html=True)
    with c4:
        st.markdown(_single_brief_card("종합 해석", briefing.get("combined_read", [])), unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    with c5:
        st.markdown(
            _split_brief_card("긍정 요인 / 부담 요인", "긍정 요인", briefing.get("positives", []), "부담 요인", briefing.get("risks", [])),
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(_single_brief_card("다음 주 체크포인트", briefing.get("checks_next_week", [])), unsafe_allow_html=True)
    st.markdown(_single_brief_card("요약", briefing.get("meeting_summary", [])), unsafe_allow_html=True)


def _render_weekly_briefing_page() -> None:
    st.subheader("3. 브리핑")
    bundle = _weekly_bundle()
    if not bundle.get("all"):
        st.info("먼저 주간 이벤트를 불러오세요.")
        return

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← 주차 선택", use_container_width=True):
            _go_prev()
            st.rerun()
    with c2:
        if st.button("브리핑 다시 생성", type="primary", use_container_width=True):
            try:
                with st.spinner("브리핑을 생성하는 중입니다..."):
                    _generate_weekly_briefing()
                st.success("브리핑 생성을 완료했습니다.")
            except Exception as exc:
                st.error(f"브리핑 생성 중 오류가 발생했습니다: {exc}")

    if st.session_state.get("generated_period_key") != _current_period_key() or not st.session_state.get("latest_weekly_briefing"):
        try:
            with st.spinner("브리핑을 준비하는 중입니다..."):
                _generate_weekly_briefing()
        except Exception as exc:
            st.error(f"브리핑 생성 중 오류가 발생했습니다: {exc}")
            return

    briefing = st.session_state["latest_weekly_briefing"]
    _render_weekly_briefing_cards(briefing)
    st.download_button(
        "브리핑 다운로드 (.md)",
        data=(st.session_state.get("latest_weekly_markdown") or "").encode("utf-8"),
        file_name=f"weekly_briefing_{_selected_company().stock_code}_{st.session_state['selected_year']}_{st.session_state['selected_month']}_{st.session_state['selected_week_no']}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    n1, n2 = st.columns(2)
    with n1:
        if st.button("← 다른 주차 보기", use_container_width=True):
            _go_prev()
            st.rerun()
    with n2:
        if st.button("회사 다시 선택", use_container_width=True):
            _go_to("search")
            st.rerun()


def main() -> None:
    _apply_theme()
    _init_state()
    _render_sidebar()
    _render_header()
    _render_progress()
    _render_summary()

    step = st.session_state.get("step", "search")
    if step == "search":
        _render_company_search_page()
    elif step == "week":
        _render_week_selector_page()
    else:
        _render_weekly_briefing_page()


if __name__ == "__main__":
    main()
