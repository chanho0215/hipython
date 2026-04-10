from __future__ import annotations

import html
import json
import os
import re
from calendar import monthrange
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import requests
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from event_briefing_service_refined import (
    CACHE_PATH,
    DART_API_KEY,
    DEFAULT_COMPANY_INDEX,
    DEFAULT_MEILI_KEY,
    DEFAULT_MEILI_URL,
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
    CompanyHit,
    EventItem,
    fetch_company_overview,
    fetch_disclosures,
    search_companies,
)


def _load_env() -> None:
    current = os.path.abspath(__file__)
    current_dir = os.path.dirname(current)
    candidates = [
        os.path.join(current_dir, ".env"),
        os.path.join(os.path.dirname(current_dir), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(current_dir)), ".env"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            load_dotenv(candidate, override=False)


_load_env()

def _get_naver_credentials() -> tuple[str, str]:
    client_id = os.getenv("NAVER_CLIENT_ID", NAVER_CLIENT_ID or "").strip()
    client_secret = os.getenv("NAVER_CLIENT_SECRET", NAVER_CLIENT_SECRET or "").strip()
    return client_id, client_secret


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(clean).replace("&quot;", '"').strip()


def _normalize_pub_date(pub_date: str) -> str:
    pub_date = (pub_date or "").strip()
    if not pub_date:
        return ""
    try:
        dt = parsedate_to_datetime(pub_date)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return pub_date[:16]


def classify_news(title: str) -> str:
    name = title or ""
    rules = [
        ("실적 기사", ["실적", "매출", "영업이익", "순이익"]),
        ("목표주가/리포트", ["목표주가", "리포트", "투자의견"]),
        ("신제품/전략", ["출시", "신제품", "AI", "전략", "파트너십"]),
        ("규제/이슈", ["소송", "규제", "제재", "과징금"]),
        ("주가 반응", ["급등", "급락", "상승", "하락"]),
    ]
    for label, keywords in rules:
        if any(keyword in name for keyword in keywords):
            return label
    return "일반 뉴스"


def _build_news_queries(company_name: str, stock_code: str, start_date: date) -> list[str]:
    month_token = f"{start_date.month}월"
    year_month_token = f"{start_date.year}년 {start_date.month}월"
    candidates = []
    if stock_code:
        candidates.extend([
            f'"{company_name}" {stock_code}',
            f'"{company_name}" {stock_code} 공시',
            f'"{company_name}" {stock_code} 실적',
        ])
    candidates.extend([
        f'"{company_name}" 공시',
        f'"{company_name}" 실적',
        f'"{company_name}" 주가',
        f'"{company_name}" {month_token}',
        f'"{company_name}" {year_month_token}',
        f'"{company_name}"',
        company_name,
    ])
    ordered: list[str] = []
    seen: set[str] = set()
    for query in candidates:
        normalized = query.strip()
        if normalized and normalized not in seen:
            ordered.append(normalized)
            seen.add(normalized)
    return ordered


def fetch_naver_news_for_date_range(
    company_name: str,
    stock_code: str,
    start_date: date,
    end_date: date,
    limit: int = 30,
    max_pages_per_query: int = 10,
) -> tuple[list[EventItem], dict[str, Any]]:
    client_id, client_secret = _get_naver_credentials()
    debug: dict[str, Any] = {
        "enabled": bool(client_id and client_secret),
        "attempts": [],
        "total_unique": 0,
        "warning": "",
    }
    if not client_id or not client_secret:
        debug["warning"] = "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 없어 뉴스 수집을 건너뛰었습니다."
        return [], debug

    collected: list[EventItem] = []
    seen_keys: set[tuple[str, str]] = set()

    days_gap = max((date.today() - start_date).days, 0)
    adaptive_pages = max_pages_per_query if days_gap <= 7 else min(10, max_pages_per_query + min(days_gap // 7, 5))

    for query in _build_news_queries(company_name, stock_code, start_date):
        page_start = 1
        for _ in range(adaptive_pages):
            try:
                response = requests.get(
                    "https://openapi.naver.com/v1/search/news.json",
                    params={
                        "query": query,
                        "display": 100,
                        "start": page_start,
                        "sort": "date",
                    },
                    headers={
                        "X-Naver-Client-Id": client_id,
                        "X-Naver-Client-Secret": client_secret,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                debug["attempts"].append({"query": query, "start": page_start, "error": str(exc), "added": 0, "total": 0, "oldest": ""})
                break

            items = data.get("items", []) or []
            total = int(data.get("total", 0) or 0)
            added = 0
            page_oldest: date | None = None

            for row in items:
                title = _strip_html(str(row.get("title", "")))
                snippet = _strip_html(str(row.get("description", "")))
                url = str(row.get("originallink") or row.get("link") or "").strip()
                pub_date_raw = str(row.get("pubDate", "")).strip()
                occurred_at = _normalize_pub_date(pub_date_raw)
                item_date = _parse_event_date(occurred_at)
                if item_date is None:
                    continue
                if page_oldest is None or item_date < page_oldest:
                    page_oldest = item_date
                if not (start_date <= item_date <= end_date):
                    continue
                key = (title, url)
                if not title or key in seen_keys:
                    continue
                seen_keys.add(key)
                collected.append(
                    EventItem(
                        event_id=f"naver:{stock_code or company_name}:{len(collected) + 1}",
                        source="뉴스",
                        occurred_at=occurred_at,
                        company_name=company_name,
                        stock_code=stock_code,
                        title=title,
                        category=classify_news(title),
                        url=url,
                        snippet=snippet,
                        meta={
                            "query": query,
                            "pubDate": pub_date_raw,
                            "originallink": row.get("originallink"),
                            "link": row.get("link"),
                        },
                    )
                )
                added += 1
                if len(collected) >= limit:
                    break

            debug["attempts"].append({
                "query": query,
                "start": page_start,
                "error": "",
                "added": added,
                "total": total,
                "oldest": page_oldest.isoformat() if page_oldest else "",
            })

            if len(collected) >= limit:
                break
            if not items:
                break
            if page_oldest and page_oldest < start_date:
                break
            if page_start + 100 > 1000:
                break
            page_start += 100

        if len(collected) >= limit:
            break

    collected = sorted(collected, key=lambda item: item.occurred_at, reverse=True)[:limit]
    debug["total_unique"] = len(collected)
    if not collected:
        debug["warning"] = "뉴스 API 호출은 성공했지만 선택한 주차 범위에 들어오는 기사를 찾지 못했습니다. 기사량이 많은 종목은 더 구체적인 검색어와 더 많은 페이지 탐색이 필요할 수 있습니다."
    debug["adaptive_pages"] = adaptive_pages
    return collected, debug

WEEKLY_BRIEFING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
당신은 한국 상장사의 특정 주간 이슈를 공시와 뉴스 기준으로 종합 브리핑하는 분석가입니다.

원칙:
- 한국어로 작성합니다.
- 제공된 자료만 사용합니다.
- 사실과 해석을 구분합니다.
- 같은 이슈를 뉴스와 공시가 함께 다룬 경우 하나의 흐름으로 묶어 설명합니다.
- 과장, 투자 권유, 감정적 표현은 피합니다.
- 출력은 반드시 하나의 JSON 객체만 반환합니다.
- 코드펜스와 설명 문장은 절대 쓰지 않습니다.

반환 JSON 스키마:
{{
  "title": "문자열",
  "week_label": "문자열",
  "one_line_summary": "문자열",
  "top_themes": ["문자열", "문자열", "문자열"],
  "disclosure_highlights": ["문자열", ...],
  "news_highlights": ["문자열", ...],
  "combined_read": ["문자열", ...],
  "positives": ["문자열", ...],
  "risks": ["문자열", ...],
  "checks_next_week": ["문자열", ...],
  "meeting_summary": ["문자열", ...]
}}
            """.strip(),
        ),
        (
            "human",
            """
브리핑 대상: {company_name} ({stock_code})
브리핑 기간: {week_label}
브리핑 목적: {brief_goal}

[회사 개황 요약]
{overview_block}

[주간 공시 목록]
{disclosure_block}

[주간 뉴스 목록]
{news_block}

[주간 전체 이벤트 타임라인]
{timeline_block}
            """.strip(),
        ),
    ]
)


def _clean_llm_json(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _coerce_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [line.strip(" -•") for line in value.splitlines() if line.strip()]
    return []


def _normalize_payload(payload: dict[str, Any], week_label: str, company_name: str) -> dict[str, Any]:
    return {
        "title": str(payload.get("title", f"{company_name} 주간 브리핑")).strip(),
        "week_label": str(payload.get("week_label", week_label)).strip(),
        "one_line_summary": str(payload.get("one_line_summary", "")).strip(),
        "top_themes": _coerce_list(payload.get("top_themes"))[:3],
        "disclosure_highlights": _coerce_list(payload.get("disclosure_highlights")),
        "news_highlights": _coerce_list(payload.get("news_highlights")),
        "combined_read": _coerce_list(payload.get("combined_read")),
        "positives": _coerce_list(payload.get("positives")),
        "risks": _coerce_list(payload.get("risks")),
        "checks_next_week": _coerce_list(payload.get("checks_next_week")),
        "meeting_summary": _coerce_list(payload.get("meeting_summary")),
    }


def valid_weeks_for_month(year: int, month: int) -> list[int]:
    last_day = monthrange(year, month)[1]
    weeks = ((last_day - 1) // 7) + 1
    return list(range(1, weeks + 1))


def _month_last_day(year: int, month: int) -> date:
    return date(year, month, monthrange(year, month)[1])


def month_week_date_range(year: int, month: int, week_no: int) -> tuple[date, date]:
    valid = valid_weeks_for_month(year, month)
    if week_no not in valid:
        raise ValueError("선택한 월에 없는 주차입니다.")
    start_day = 1 + (week_no - 1) * 7
    start_dt = date(year, month, start_day)
    end_day = min(start_day + 6, monthrange(year, month)[1])
    end_dt = date(year, month, end_day)
    return start_dt, end_dt


def week_label(year: int, month: int, week_no: int) -> str:
    return f"{year}년 {month}월 {week_no}주차"


def _parse_event_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    normalized = text[:16]
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(normalized[: len(datetime.now().strftime(fmt))], fmt).date()
        except Exception:
            continue
    # fallback for strings like 'Tue, 18 Mar 2025 15:04:00 +0900'
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            continue
    if len(text) >= 10:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    return None


def _filter_events_in_range(items: list[EventItem], start_date: date, end_date: date) -> list[EventItem]:
    filtered: list[EventItem] = []
    for item in items:
        item_date = _parse_event_date(item.occurred_at)
        if item_date and start_date <= item_date <= end_date:
            filtered.append(item)
    return filtered


def fetch_company_events_for_month_week(
    corp_code: str,
    company_name: str,
    stock_code: str,
    year: int,
    month: int,
    week_no: int,
    disclosure_limit: int = 40,
    news_limit: int = 30,
) -> dict[str, Any]:
    start_date, end_date = month_week_date_range(year, month, week_no)

    days_back = max((date.today() - start_date).days + 10, 45)
    disclosures = fetch_disclosures(
        corp_code=corp_code,
        company_name=company_name,
        stock_code=stock_code,
        days=days_back,
        limit=disclosure_limit,
    )
    news, news_debug = fetch_naver_news_for_date_range(
        company_name=company_name,
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        limit=news_limit,
    )

    disclosures = _filter_events_in_range(disclosures, start_date, end_date)
    all_events = sorted(disclosures + news, key=lambda item: item.occurred_at, reverse=True)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "week_label": week_label(year, month, week_no),
        "selected_year": year,
        "selected_month": month,
        "selected_week_no": week_no,
        "disclosures": disclosures,
        "news": news,
        "all": all_events,
        "news_debug": news_debug,
    }


def _overview_block(overview: dict[str, Any] | None) -> str:
    if not overview:
        return "회사 개황 데이터 없음"
    keys = [
        ("corp_name", "회사명"),
        ("stock_name", "종목명"),
        ("stock_code", "종목코드"),
        ("ceo_nm", "대표자"),
        ("corp_cls", "시장구분"),
        ("induty_code", "업종코드"),
        ("est_dt", "설립일"),
        ("acc_mt", "결산월"),
    ]
    rows = []
    for key, label in keys:
        value = str(overview.get(key, "")).strip()
        if value:
            rows.append(f"- {label}: {value}")
    return "\n".join(rows) if rows else "회사 개황 데이터 없음"


def _events_block(items: list[EventItem], empty_message: str) -> str:
    if not items:
        return empty_message
    lines = []
    for idx, item in enumerate(items, start=1):
        lines.append(
            f"{idx}. [{item.source}] {item.occurred_at} | {item.category} | {item.title}\n"
            f"   - 요약: {item.snippet or '요약 없음'}"
        )
    return "\n".join(lines)


def _timeline_block(all_events: list[EventItem]) -> str:
    if not all_events:
        return "해당 주간 이벤트 없음"
    return "\n".join(
        f"- {item.occurred_at} | {item.source} | {item.category} | {item.title}" for item in all_events
    )


def generate_weekly_briefing_structured(
    company_name: str,
    stock_code: str,
    week_label: str,
    overview: dict[str, Any] | None,
    disclosures: list[EventItem],
    news: list[EventItem],
    all_events: list[EventItem],
    brief_goal: str = "해당 주간의 공시와 뉴스 흐름을 함께 묶어 회의용 브리핑으로 정리",
) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
    )
    prompt_value = WEEKLY_BRIEFING_PROMPT.invoke(
        {
            "company_name": company_name,
            "stock_code": stock_code,
            "week_label": week_label,
            "brief_goal": brief_goal,
            "overview_block": _overview_block(overview),
            "disclosure_block": _events_block(disclosures, "해당 주간 공시 없음"),
            "news_block": _events_block(news, "해당 주간 뉴스 없음"),
            "timeline_block": _timeline_block(all_events),
        }
    )
    response = llm.invoke(prompt_value)
    raw = _clean_llm_json(str(response.content))
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {
            "title": f"{company_name} {week_label} 브리핑",
            "week_label": week_label,
            "one_line_summary": raw.splitlines()[0] if raw else "브리핑 생성 결과를 구조화하지 못했습니다.",
            "top_themes": [],
            "disclosure_highlights": _coerce_list(raw),
            "news_highlights": [],
            "combined_read": [],
            "positives": [],
            "risks": [],
            "checks_next_week": [],
            "meeting_summary": [],
        }
    return _normalize_payload(payload, week_label, company_name)


def weekly_briefing_to_markdown(briefing: dict[str, Any]) -> str:
    sections = [
        ("핵심 이슈 TOP 3", briefing.get("top_themes", [])),
        ("공시 하이라이트", briefing.get("disclosure_highlights", [])),
        ("뉴스 하이라이트", briefing.get("news_highlights", [])),
        ("종합 해석", briefing.get("combined_read", [])),
        ("긍정 요인", briefing.get("positives", [])),
        ("부담 요인", briefing.get("risks", [])),
        ("다음 주 체크포인트", briefing.get("checks_next_week", [])),
        ("회의용 5줄 요약", briefing.get("meeting_summary", [])),
    ]
    lines = [
        f"# {briefing.get('title', '주간 브리핑')}",
        "",
        f"**기간**: {briefing.get('week_label', '-')}",
        "",
        f"**한줄 요약**\n{briefing.get('one_line_summary', '-')}",
        "",
    ]
    for title, items in sections:
        lines.append(f"## {title}")
        if items:
            lines.extend([f"- {item}" for item in items])
        else:
            lines.append("- 해당 사항 없음")
        lines.append("")
    return "\n".join(lines).strip()
