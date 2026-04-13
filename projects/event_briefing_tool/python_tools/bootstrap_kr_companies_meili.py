from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from meilisearch import Client

from event_briefing_service_refined import (
    CACHE_PATH,
    DEFAULT_COMPANY_INDEX,
    DEFAULT_MEILI_KEY,
    DEFAULT_MEILI_URL,
    download_corp_codes,
)


def _load_env() -> None:
    # 단독 실행 스크립트라 현재 폴더 기준으로 .env를 찾는 편이 편하다.
    current = Path(__file__).resolve()
    for candidate in (
        current.parent / ".env",
        current.parent.parent / ".env",
        current.parent.parent.parent / ".env",
    ):
        if candidate.exists():
            load_dotenv(candidate, override=False)


_load_env()


def main() -> None:
    docs = download_corp_codes()
    meili_key = os.getenv("MEILISEARCH_API_KEY") or os.getenv("MEILISEARCH_MASTER_KEY") or DEFAULT_MEILI_KEY
    index_name = os.getenv("COMPANY_INDEX") or os.getenv("MEILISEARCH_COMPANY_INDEX") or DEFAULT_COMPANY_INDEX
    client = Client(os.getenv("MEILISEARCH_URL", DEFAULT_MEILI_URL), meili_key)
    index = client.index(index_name)
    try:
        # 인덱스를 통째로 다시 채우는 방식이라 예전 문서는 먼저 비운다.
        index.delete_all_documents()
    except Exception:
        pass
    # 회사 검색은 이름/티커/고유코드 세 축만 잘 잡히면 충분하다.
    index.update_searchable_attributes(["corp_name", "stock_code", "corp_code"])
    index.update_filterable_attributes(["corp_cls", "stock_code"])
    task = index.add_documents(docs, primary_key="corp_code")
    task_uid = getattr(task, "task_uid", None)
    if task_uid is None and isinstance(task, dict):
        task_uid = task.get("taskUid")
    print(f"indexed={len(docs)}")
    print(f"index_name={index_name}")
    print(f"task_uid={task_uid}")
    print(f"cache_path={CACHE_PATH}")


if __name__ == "__main__":
    main()
