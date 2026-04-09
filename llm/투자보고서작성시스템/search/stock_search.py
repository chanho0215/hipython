from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

try:
    from meilisearch import Client
except ImportError:  # pragma: no cover
    Client = None  # type: ignore[assignment]


def _load_env() -> None:
    current = Path(__file__).resolve()
    for candidate in (
        current.parents[2] / ".env",
        current.parents[1] / ".env",
        current.parents[3] / ".env",
    ):
        if candidate.exists():
            load_dotenv(candidate, override=False)


_load_env()

DEFAULT_MEILI_URL = os.getenv("MEILISEARCH_URL", "http://127.0.0.1:7700")
DEFAULT_MEILI_KEY = os.getenv("MEILISEARCH_MASTER_KEY")
DEFAULT_INDEX_NAME = os.getenv("MEILISEARCH_INDEX", "nasdaq")

FALLBACK_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc. Common Stock", "exchange": "NASDAQ"},
    {"symbol": "MSFT", "name": "Microsoft Corporation Common Stock", "exchange": "NASDAQ"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation Common Stock", "exchange": "NASDAQ"},
    {"symbol": "AMZN", "name": "Amazon.com, Inc. Common Stock", "exchange": "NASDAQ"},
    {"symbol": "META", "name": "Meta Platforms, Inc. Class A Common Stock", "exchange": "NASDAQ"},
    {"symbol": "TSLA", "name": "Tesla, Inc. Common Stock", "exchange": "NASDAQ"},
    {"symbol": "GOOGL", "name": "Alphabet Inc. Class A Common Stock", "exchange": "NASDAQ"},
    {"symbol": "AMD", "name": "Advanced Micro Devices, Inc. Common Stock", "exchange": "NASDAQ"},
    {"symbol": "NFLX", "name": "Netflix, Inc. Common Stock", "exchange": "NASDAQ"},
    {"symbol": "INTC", "name": "Intel Corporation Common Stock", "exchange": "NASDAQ"},
]


def _normalize_hit(hit: dict[str, Any]) -> dict[str, str]:
    symbol = str(hit.get("symbol") or hit.get("Symbol") or "").strip().upper()
    name = str(hit.get("name") or hit.get("Name") or "").strip()
    exchange = str(hit.get("exchange") or hit.get("Exchange") or "NASDAQ").strip()
    return {"symbol": symbol, "name": name, "exchange": exchange}


def _fallback_search(query: str, limit: int) -> dict[str, Any]:
    lowered_query = query.lower().strip()
    hits = [
        stock
        for stock in FALLBACK_STOCKS
        if lowered_query in stock["symbol"].lower() or lowered_query in stock["name"].lower()
    ][:limit]
    return {
        "hits": hits,
        "source": "fallback",
        "message": "Meilisearch 연결이 원활하지 않아 기본 후보 목록으로 대체했습니다.",
        "error_type": "fallback",
        "details": "",
        "index_name": DEFAULT_INDEX_NAME,
        "meili_url": DEFAULT_MEILI_URL,
    }


def stock_search(query: str, limit: int = 10) -> dict[str, Any]:
    query = query.strip()
    if not query:
        return {
            "hits": [],
            "source": "empty",
            "message": "회사명 또는 티커를 입력해 주세요.",
            "error_type": "",
            "details": "",
            "index_name": DEFAULT_INDEX_NAME,
            "meili_url": DEFAULT_MEILI_URL,
        }

    if Client is None:
        return _fallback_search(query, limit)

    try:
        client = Client(DEFAULT_MEILI_URL, DEFAULT_MEILI_KEY)
        result = client.index(DEFAULT_INDEX_NAME).search(
            query,
            {
                "attributesToSearchOn": ["symbol", "name", "Symbol", "Name"],
                "limit": limit,
                "matchingStrategy": "all",
            },
        )

        normalized_hits: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for raw_hit in result.get("hits", []):
            hit = _normalize_hit(raw_hit)
            key = (hit["symbol"], hit["name"])
            if hit["symbol"] and hit["name"] and key not in seen:
                normalized_hits.append(hit)
                seen.add(key)

        return {
            "hits": normalized_hits,
            "source": "meilisearch",
            "message": f"Meilisearch 인덱스 `{DEFAULT_INDEX_NAME}`에서 검색 결과를 불러왔습니다.",
            "error_type": "",
            "details": "",
            "index_name": DEFAULT_INDEX_NAME,
            "meili_url": DEFAULT_MEILI_URL,
        }
    except Exception as exc:  # pragma: no cover
        fallback = _fallback_search(query, limit)
        error_text = str(exc)
        error_type = "connection_error"
        if "index_not_found" in error_text.lower():
            error_type = "index_not_found"
            fallback["message"] = f"Meilisearch 인덱스 `{DEFAULT_INDEX_NAME}`를 찾지 못해 기본 후보 목록으로 대체했습니다."
        else:
            fallback["message"] = "검색 엔진 연결에 문제가 있어 기본 후보 목록으로 대체했습니다."
        fallback["error_type"] = error_type
        fallback["details"] = error_text
        return fallback
