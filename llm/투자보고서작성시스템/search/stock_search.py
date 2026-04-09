from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

try:
    from meilisearch import Client
except ImportError:  # pragma: no cover - dependency may be intentionally missing
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
        "message": "흥, Meilisearch 쪽이 잠깐 비틀거렸네. 그래도 멈출 생각은 없으니까 비상용 데모 데이터로 먼저 후보를 끌어왔어.",
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
            "message": "어이, 검색어부터 넣어. 종목도 안 던져주고 결론부터 바라면 곤란하거든.",
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
            "message": f"좋아, Meilisearch 인덱스 `{DEFAULT_INDEX_NAME}`에서 후보를 깔끔하게 추렸어. 이제 고르기만 하면 돼.",
            "error_type": "",
            "details": "",
            "index_name": DEFAULT_INDEX_NAME,
            "meili_url": DEFAULT_MEILI_URL,
        }
    except Exception as exc:  # pragma: no cover - depends on external server state
        fallback = _fallback_search(query, limit)
        error_text = str(exc)
        error_type = "connection_error"
        if "index_not_found" in error_text.lower():
            error_type = "index_not_found"
            fallback["message"] = (
                f"흥, `{DEFAULT_INDEX_NAME}` 인덱스가 아직 비어 있거나 안 만들어졌네. "
                "그래서 우선은 내가 숨겨둔 데모 후보로 화면을 살려둘게."
            )
        else:
            fallback["message"] = (
                "Meilisearch 연결이 흔들렸어. 그래도 여기서 멈추면 재미없잖아. "
                "일단 데모 데이터로 검색 후보를 이어서 보여줄게."
            )
        fallback["error_type"] = error_type
        fallback["details"] = error_text
        return fallback
