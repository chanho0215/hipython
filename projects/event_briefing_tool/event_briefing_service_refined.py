from __future__ import annotations

import html
import json
import os
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import requests
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

try:
    from meilisearch import Client
except ImportError:  # pragma: no cover
    Client = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parent
CACHE_PATH = ROOT / "kr_companies_cache.json"


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

DEFAULT_MEILI_URL = os.getenv("MEILISEARCH_URL", "http://127.0.0.1:7700")
DEFAULT_MEILI_KEY = os.getenv("MEILISEARCH_MASTER_KEY")
DEFAULT_COMPANY_INDEX = os.getenv("MEILISEARCH_COMPANY_INDEX", "kr_companies")
DART_API_KEY = os.getenv("DART_API_KEY") or os.getenv("OPENDART_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


@dataclass(frozen=True)
class CompanyHit:
    corp_code: str
    corp_name: str
    stock_code: str
    corp_cls: str = ""
    modify_date: str = ""

    @property
    def label(self) -> str:
        market = {"Y": "KOSPI", "K": "KOSDAQ", "N": "KONEX", "E": "기타"}.get(self.corp_cls, self.corp_cls or "-")
        stock = self.stock_code or "비상장"
        return f"{self.corp_name} | {stock} | {market}"


@dataclass(frozen=True)
class EventItem:
    event_id: str
    source: str
    occurred_at: str
    company_name: str
    stock_code: str
    title: str
    category: str
    url: str
    snippet: str
    meta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


BRIEFING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
당신은 한국 상장사 이벤트 브리핑을 작성하는 분석가입니다.

원칙:
- 한국어로 작성합니다.
- 오직 제공된 자료만 사용합니다.
- 사실과 해석을 분리합니다.
- 과장, 감정적 표현, 투자 권유식 문장은 피합니다.
- 출력은 반드시 하나의 JSON 객체만 반환합니다.
- 코드펜스와 설명 문장은 절대 쓰지 않습니다.

반환 JSON 스키마:
{{
  "title": "문자열",
  "one_line_summary": "문자열",
  "confirmed_facts": ["문자열", ...],
  "original_points": ["문자열", ...],
  "market_interpretation": ["문자열", ...],
  "positives": ["문자열", ...],
  "risks": ["문자열", ...],
  "checks": ["문자열", ...],
  "meeting_summary": ["문자열", ...]
}}
            """.strip(),
        ),
        (
            "human",
            """
브리핑 대상: {company_name} ({stock_code})
브리핑 모드: {brief_mode}
보고 목적: {brief_goal}

[선택 이벤트]
출처: {source}
일시: {occurred_at}
분류: {category}
제목: {title}
요약: {snippet}
세부 메타데이터: {meta_json}

[선택 공시 원문 파싱 결과]
{original_doc_block}

[주변 이벤트]
{context_block}
            """.strip(),
        ),
    ]
)


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(clean).replace("&quot;", '"').strip()


def _safe_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _load_local_cache() -> list[dict[str, str]]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return []


def _normalize_company_hit(raw: dict[str, Any]) -> dict[str, str]:
    return {
        "corp_code": str(raw.get("corp_code", "")).strip(),
        "corp_name": str(raw.get("corp_name", "")).strip(),
        "stock_code": str(raw.get("stock_code", "")).strip(),
        "corp_cls": str(raw.get("corp_cls", "")).strip(),
        "modify_date": str(raw.get("modify_date", "")).strip(),
    }


def search_companies(query: str, limit: int = 10) -> dict[str, Any]:
    query = query.strip()
    if not query:
        return {
            "hits": [],
            "source": "empty",
            "message": "회사명 또는 종목코드를 입력해 주세요.",
            "index_name": DEFAULT_COMPANY_INDEX,
            "details": "",
        }

    details = ""
    if Client is not None:
        try:
            client = Client(DEFAULT_MEILI_URL, DEFAULT_MEILI_KEY)
            result = client.index(DEFAULT_COMPANY_INDEX).search(
                query,
                {
                    "attributesToSearchOn": ["corp_name", "stock_code", "corp_code"],
                    "limit": limit,
                    "matchingStrategy": "all",
                },
            )
            hits = []
            seen: set[tuple[str, str]] = set()
            for raw_hit in result.get("hits", []):
                hit = _normalize_company_hit(raw_hit)
                key = (hit["corp_code"], hit["corp_name"])
                if hit["corp_name"] and key not in seen:
                    hits.append(hit)
                    seen.add(key)
            if hits:
                return {
                    "hits": hits,
                    "source": "meilisearch",
                    "message": f"Meilisearch 인덱스 `{DEFAULT_COMPANY_INDEX}`에서 검색했습니다.",
                    "index_name": DEFAULT_COMPANY_INDEX,
                    "details": "",
                }
        except Exception as exc:  # pragma: no cover
            details = str(exc)
    else:
        details = "meilisearch 패키지가 설치되어 있지 않습니다."

    cache = _load_local_cache()
    if cache:
        lowered = query.lower()
        hits = [
            item
            for item in cache
            if lowered in item.get("corp_name", "").lower() or lowered in item.get("stock_code", "").lower()
        ][:limit]
        return {
            "hits": hits,
            "source": "cache",
            "message": "Meilisearch 연결이 없어 로컬 회사 캐시로 검색했습니다.",
            "index_name": DEFAULT_COMPANY_INDEX,
            "details": details,
        }

    return {
        "hits": [],
        "source": "unavailable",
        "message": "회사 검색 인덱스가 아직 없습니다. bootstrap 스크립트로 회사 인덱스를 먼저 준비해 주세요.",
        "index_name": DEFAULT_COMPANY_INDEX,
        "details": details,
    }



def _require_dart_key() -> str:
    if not DART_API_KEY:
        raise RuntimeError("DART_API_KEY 또는 OPENDART_API_KEY가 설정되어 있지 않습니다.")
    return DART_API_KEY


def download_corp_codes() -> list[dict[str, str]]:
    key = _require_dart_key()
    listed_only = os.getenv("DART_LISTED_ONLY", "true").strip().lower() not in {"0", "false", "no"}
    response = requests.get(
        "https://opendart.fss.or.kr/api/corpCode.xml",
        params={"crtfc_key": key},
        timeout=60,
    )
    response.raise_for_status()
    with zipfile.ZipFile(BytesIO(response.content)) as zf:
        xml_name = next(name for name in zf.namelist() if name.lower().endswith(".xml"))
        xml_bytes = zf.read(xml_name)

    root = ET.fromstring(xml_bytes)
    documents: list[dict[str, str]] = []
    for item in root.findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        corp_code = (item.findtext("corp_code") or "").strip()
        corp_name = (item.findtext("corp_name") or "").strip()
        modify_date = (item.findtext("modify_date") or "").strip()
        if not corp_name:
            continue
        if listed_only and not stock_code:
            continue
        corp_cls = "Y" if stock_code else "E"
        documents.append(
            {
                "corp_code": corp_code,
                "corp_name": corp_name,
                "stock_code": stock_code,
                "corp_cls": corp_cls,
            }
        )
    # Keep the cache compact so it can be uploaded to hosts with strict file-size limits.
    CACHE_PATH.write_text(json.dumps(documents, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return documents


def fetch_company_overview(corp_code: str) -> dict[str, Any]:
    key = _require_dart_key()
    response = requests.get(
        "https://opendart.fss.or.kr/api/company.json",
        params={"crtfc_key": key, "corp_code": corp_code},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "000":
        raise RuntimeError(data.get("message", "기업 개황 조회에 실패했습니다."))
    return data


def classify_disclosure(report_name: str) -> str:
    name = report_name or ""
    rules = [
        ("실적", ["사업보고서", "분기보고서", "반기보고서", "감사보고서"]),
        ("자사주", ["자기주식", "신탁계약"]),
        ("주주환원", ["배당", "소각"]),
        ("M&A/투자", ["합병", "양수", "양도", "출자", "취득", "처분"]),
        ("자금조달", ["증자", "사채", "전환사채", "신주인수권부사채"]),
        ("지배구조", ["주주총회", "대표이사", "임원", "최대주주"]),
        ("소송/규제", ["소송", "과징금", "영업정지", "회생", "파산"]),
    ]
    for label, keywords in rules:
        if any(keyword in name for keyword in keywords):
            return label
    return "기타 공시"


def fetch_disclosures(corp_code: str, company_name: str, stock_code: str, days: int = 30, limit: int = 12) -> list[EventItem]:
    key = _require_dart_key()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    response = requests.get(
        "https://opendart.fss.or.kr/api/list.json",
        params={
            "crtfc_key": key,
            "corp_code": corp_code,
            "bgn_de": start_date.strftime("%Y%m%d"),
            "end_de": end_date.strftime("%Y%m%d"),
            "last_reprt_at": "Y",
            "sort": "date",
            "sort_mth": "desc",
            "page_no": 1,
            "page_count": min(limit, 100),
        },
        timeout=40,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") not in {"000", "013"}:
        raise RuntimeError(data.get("message", "공시 목록 조회에 실패했습니다."))

    items: list[EventItem] = []
    for row in data.get("list", []):
        rcp_no = str(row.get("rcept_no", ""))
        report_nm = str(row.get("report_nm", "")).strip()
        rcept_dt = str(row.get("rcept_dt", "")).strip()
        occurred_at = f"{rcept_dt[:4]}-{rcept_dt[4:6]}-{rcept_dt[6:8]}" if len(rcept_dt) == 8 else rcept_dt
        snippet = f"{row.get('flr_nm', '')} 제출 · {row.get('rm', '')}".strip(" ·")
        items.append(
            EventItem(
                event_id=f"dart:{rcp_no}",
                source="공시",
                occurred_at=occurred_at,
                company_name=company_name,
                stock_code=stock_code,
                title=report_nm,
                category=classify_disclosure(report_nm),
                url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}" if rcp_no else "",
                snippet=snippet or "공시 메타데이터 기반 이벤트",
                meta={
                    "corp_code": row.get("corp_code"),
                    "corp_cls": row.get("corp_cls"),
                    "report_nm": report_nm,
                    "rcept_no": rcp_no,
                    "rcept_dt": rcept_dt,
                    "flr_nm": row.get("flr_nm"),
                    "rm": row.get("rm"),
                },
            )
        )
    return items


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


def _normalize_pub_date(pub_date: str) -> str:
    pub_date = (pub_date or "").strip()
    if not pub_date:
        return ""
    try:
        dt = parsedate_to_datetime(pub_date)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return pub_date[:16]


def _build_news_queries(company_name: str, stock_code: str) -> list[str]:
    candidates = [
        company_name,
        f'"{company_name}" 주가',
        f'"{company_name}" 공시',
        f'"{company_name}" 실적',
    ]
    if stock_code:
        candidates.extend(
            [
                f'"{company_name}" {stock_code}',
                stock_code,
            ]
        )
    ordered: list[str] = []
    seen: set[str] = set()
    for query in candidates:
        normalized = query.strip()
        if normalized and normalized not in seen:
            ordered.append(normalized)
            seen.add(normalized)
    return ordered


def fetch_naver_news(company_name: str, stock_code: str, limit: int = 6) -> tuple[list[EventItem], dict[str, Any]]:
    debug: dict[str, Any] = {
        "enabled": bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET),
        "attempts": [],
        "total_unique": 0,
        "warning": "",
    }
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        debug["warning"] = "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 없어 뉴스 수집을 건너뛰었습니다."
        return [], debug

    collected: list[EventItem] = []
    seen_keys: set[tuple[str, str]] = set()
    queries = _build_news_queries(company_name, stock_code)
    for query in queries:
        try:
            response = requests.get(
                "https://openapi.naver.com/v1/search/news.json",
                params={
                    "query": query,
                    "display": min(max(limit * 2, 10), 100),
                    "start": 1,
                    "sort": "date",
                },
                headers={
                    "X-Naver-Client-Id": NAVER_CLIENT_ID,
                    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            debug["attempts"].append({"query": query, "error": str(exc), "added": 0, "total": 0})
            continue

        added = 0
        total = int(data.get("total", 0) or 0)
        for row in data.get("items", []):
            title = _strip_html(str(row.get("title", "")))
            snippet = _strip_html(str(row.get("description", "")))
            url = str(row.get("originallink") or row.get("link") or "").strip()
            key = (title, url)
            if not title or key in seen_keys:
                continue
            seen_keys.add(key)
            pub_date = str(row.get("pubDate", "")).strip()
            collected.append(
                EventItem(
                    event_id=f"naver:{stock_code or company_name}:{len(collected) + 1}",
                    source="뉴스",
                    occurred_at=_normalize_pub_date(pub_date),
                    company_name=company_name,
                    stock_code=stock_code,
                    title=title,
                    category=classify_news(title),
                    url=url,
                    snippet=snippet,
                    meta={
                        "query": query,
                        "pubDate": pub_date,
                        "originallink": row.get("originallink"),
                        "link": row.get("link"),
                    },
                )
            )
            added += 1
            if len(collected) >= limit:
                break

        debug["attempts"].append({"query": query, "error": "", "added": added, "total": total})
        if len(collected) >= limit:
            break

    debug["total_unique"] = len(collected)
    if not collected:
        debug["warning"] = "뉴스 API 호출은 되었지만 조건에 맞는 결과를 확보하지 못했습니다. 검색어를 더 단순하게 바꾸거나 회사명 기반으로 다시 확인해 보세요."
    return collected[:limit], debug


def fetch_company_events(
    corp_code: str,
    company_name: str,
    stock_code: str,
    days: int = 30,
    disclosure_limit: int = 12,
    news_limit: int = 6,
) -> dict[str, Any]:
    disclosures = fetch_disclosures(corp_code, company_name, stock_code, days=days, limit=disclosure_limit)
    news, news_debug = fetch_naver_news(company_name, stock_code, limit=news_limit)
    all_events = sorted(disclosures + news, key=lambda item: str(item.occurred_at), reverse=True)
    return {
        "all": all_events,
        "disclosures": disclosures,
        "news": news,
        "news_debug": news_debug,
    }


def _best_effort_decode(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _strip_tags_with_breaks(text: str) -> str:
    text = re.sub(r"<(br|BR)\s*/?>", "\n", text)
    text = re.sub(r"</(p|P|div|DIV|tr|TR|table|TABLE|li|LI|h1|H1|h2|H2|h3|H3|title|TITLE)>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return _normalize_text(text)


def _extract_text_from_xml(raw_text: str) -> str:
    try:
        root = ET.fromstring(raw_text)
    except ET.ParseError:
        return _strip_tags_with_breaks(raw_text)

    blocks: list[str] = []
    for elem in root.iter():
        tag = str(elem.tag).split("}")[-1].lower()
        text = " ".join((elem.text or "").split())
        if not text:
            continue
        if tag in {"title", "subtitle", "h1", "h2", "h3", "h4"}:
            blocks.append(f"\n## {text}\n")
        elif tag in {"p", "span", "li", "td", "th", "dd", "dt"}:
            blocks.append(text)
    joined = "\n".join(blocks)
    cleaned = _normalize_text(joined)
    return cleaned if len(cleaned) >= 300 else _strip_tags_with_breaks(raw_text)


def _choose_candidate_files(zf: zipfile.ZipFile) -> list[str]:
    candidates: list[tuple[int, str]] = []
    for name in zf.namelist():
        lower = name.lower()
        if any(lower.endswith(ext) for ext in (".xml", ".xhtml", ".html", ".htm", ".txt")):
            if any(skip in lower for skip in ("image", "img", "photo", "signature", "sign")):
                continue
            info = zf.getinfo(name)
            candidates.append((info.file_size, name))
    candidates.sort(reverse=True)
    return [name for _, name in candidates[:5]]


def _paragraphs_from_text(text: str) -> list[str]:
    parts = re.split(r"\n{2,}", text)
    paragraphs = [re.sub(r"\s+", " ", part).strip() for part in parts]
    return [p for p in paragraphs if len(p) >= 20]


def _looks_like_heading(paragraph: str) -> bool:
    if len(paragraph) > 80:
        return False
    if paragraph.count(" ") > 6:
        return False
    return bool(
        re.match(r"^((제\s*\d+\s*부)|(제\s*\d+\s*장)|(제\s*\d+\s*절)|([IVX]+\.)|(\d+\.)|([가-힣]\.)).+", paragraph)
        or re.match(r"^[가-힣A-Za-z0-9][가-힣A-Za-z0-9\s\-/()]{2,40}$", paragraph)
    )


def _sectionize_text(text: str, max_sections: int = 8, max_chars: int = 9000) -> list[dict[str, str]]:
    paragraphs = _paragraphs_from_text(text)
    if not paragraphs:
        return []

    sections: list[dict[str, str]] = []
    current_heading = "본문"
    current_parts: list[str] = []
    for paragraph in paragraphs:
        if _looks_like_heading(paragraph) and current_parts:
            sections.append({"heading": current_heading, "content": "\n\n".join(current_parts)})
            current_heading = paragraph
            current_parts = []
        elif _looks_like_heading(paragraph) and not current_parts:
            current_heading = paragraph
        else:
            current_parts.append(paragraph)
    if current_parts:
        sections.append({"heading": current_heading, "content": "\n\n".join(current_parts)})

    compact: list[dict[str, str]] = []
    total = 0
    for section in sections:
        content = section["content"].strip()
        if len(content) < 40:
            continue
        remaining = max_chars - total
        if remaining <= 0:
            break
        sliced = content[:remaining]
        compact.append({"heading": section["heading"], "content": sliced})
        total += len(sliced)
        if len(compact) >= max_sections:
            break
    return compact


def parse_disclosure_original_document(rcept_no: str, max_sections: int = 8, max_chars: int = 9000) -> dict[str, Any]:
    key = _require_dart_key()
    response = requests.get(
        "https://opendart.fss.or.kr/api/document.xml",
        params={"crtfc_key": key, "rcept_no": rcept_no},
        timeout=90,
    )
    response.raise_for_status()

    content = response.content
    if not content.startswith(b"PK"):
        text = _best_effort_decode(content)
        raise RuntimeError(_strip_tags_with_breaks(text)[:300] or "공시 원문 파일을 내려받지 못했습니다.")

    with zipfile.ZipFile(BytesIO(content)) as zf:
        candidates = _choose_candidate_files(zf)
        if not candidates:
            raise RuntimeError("원문 ZIP 안에서 읽을 수 있는 XML/HTML 파일을 찾지 못했습니다.")

        best_name = ""
        best_text = ""
        for name in candidates:
            raw = zf.read(name)
            decoded = _best_effort_decode(raw)
            extracted = _extract_text_from_xml(decoded)
            if len(extracted) > len(best_text):
                best_name = name
                best_text = extracted

    cleaned = _normalize_text(best_text)
    if len(cleaned) < 200:
        raise RuntimeError("원문을 파싱했지만 추출된 본문이 너무 짧습니다.")

    sections = _sectionize_text(cleaned, max_sections=max_sections, max_chars=max_chars)
    excerpt_lines = [f"## {section['heading']}\n{section['content']}" for section in sections]
    excerpt_markdown = "\n\n".join(excerpt_lines).strip()
    return {
        "rcept_no": rcept_no,
        "source_file": best_name,
        "text_length": len(cleaned),
        "section_count": len(sections),
        "sections": sections,
        "excerpt_markdown": excerpt_markdown,
        "full_text": cleaned[: max_chars * 2],
    }


def _context_block(context_events: list[EventItem]) -> str:
    if not context_events:
        return "주변 이벤트 없음"
    lines = []
    for item in context_events[:6]:
        lines.append(f"- [{item.source}] {item.occurred_at} | {item.title} | {item.category}")
    return "\n".join(lines)


def _clean_llm_json(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json|markdown|md)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _coerce_list(data: Any, fallback: str = "") -> list[str]:
    if isinstance(data, list):
        values = [str(item).strip() for item in data if str(item).strip()]
        return values
    if isinstance(data, str) and data.strip():
        parts = [part.strip(" -•") for part in data.split("\n") if part.strip()]
        return parts
    return [fallback] if fallback else []


def _normalize_briefing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": str(payload.get("title", "이벤트 브리핑")).strip(),
        "one_line_summary": str(payload.get("one_line_summary", "")).strip(),
        "confirmed_facts": _coerce_list(payload.get("confirmed_facts")),
        "original_points": _coerce_list(payload.get("original_points")),
        "market_interpretation": _coerce_list(payload.get("market_interpretation")),
        "positives": _coerce_list(payload.get("positives")),
        "risks": _coerce_list(payload.get("risks")),
        "checks": _coerce_list(payload.get("checks")),
        "meeting_summary": _coerce_list(payload.get("meeting_summary")),
    }


def _original_doc_block(original_document: dict[str, Any] | None) -> str:
    if not original_document:
        return "원문 파싱 결과 없음"
    return (
        f"원문 파일: {original_document.get('source_file', '-') }\n"
        f"추출 길이: {original_document.get('text_length', 0)}자\n"
        f"섹션 수: {original_document.get('section_count', 0)}\n\n"
        f"{original_document.get('excerpt_markdown', '')}".strip()
    )


def generate_event_briefing_structured(
    company_name: str,
    stock_code: str,
    event: EventItem,
    context_events: list[EventItem],
    brief_mode: str = "투자자용",
    brief_goal: str = "선택 이벤트의 핵심 사실과 시장 해석 포인트를 빠르게 파악",
    original_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
    )
    prompt_value = BRIEFING_PROMPT.invoke(
        {
            "company_name": company_name,
            "stock_code": stock_code,
            "brief_mode": brief_mode,
            "brief_goal": brief_goal,
            "source": event.source,
            "occurred_at": event.occurred_at,
            "category": event.category,
            "title": event.title,
            "snippet": event.snippet,
            "meta_json": _safe_json(event.meta),
            "original_doc_block": _original_doc_block(original_document),
            "context_block": _context_block(context_events),
        }
    )
    response = llm.invoke(prompt_value)
    raw = _clean_llm_json(str(response.content))
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {
            "title": event.title,
            "one_line_summary": raw.splitlines()[0] if raw else "브리핑 생성 결과를 구조화하지 못했습니다.",
            "confirmed_facts": [raw] if raw else [],
            "original_points": [],
            "market_interpretation": [],
            "positives": [],
            "risks": [],
            "checks": [],
            "meeting_summary": [],
        }
    return _normalize_briefing_payload(payload)


def structured_briefing_to_markdown(briefing: dict[str, Any]) -> str:
    lines = [
        f"# {briefing.get('title', '이벤트 브리핑')}",
        "",
        f"**한줄 요약**\n{briefing.get('one_line_summary', '-')}",
        "",
    ]
    sections = [
        ("실제로 확인된 사실", briefing.get("confirmed_facts", [])),
        ("원문 기준 핵심 포인트", briefing.get("original_points", [])),
        ("시장 해석 포인트", briefing.get("market_interpretation", [])),
        ("긍정 요인", briefing.get("positives", [])),
        ("부담 요인", briefing.get("risks", [])),
        ("지금 추가로 확인할 것", briefing.get("checks", [])),
        ("회의용 5줄 요약", briefing.get("meeting_summary", [])),
    ]
    for heading, items in sections:
        lines.append(f"## {heading}")
        if items:
            lines.extend([f"- {item}" for item in items])
        else:
            lines.append("- 해당 사항 없음")
        lines.append("")
    return "\n".join(lines).strip()
