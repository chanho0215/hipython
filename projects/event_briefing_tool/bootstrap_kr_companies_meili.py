from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from meilisearch import Client

from event_briefing_service import CACHE_PATH, DEFAULT_COMPANY_INDEX, DEFAULT_MEILI_KEY, DEFAULT_MEILI_URL, download_corp_codes


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


def main() -> None:
    docs = download_corp_codes()
    client = Client(os.getenv("MEILISEARCH_URL", DEFAULT_MEILI_URL), os.getenv("MEILISEARCH_MASTER_KEY", DEFAULT_MEILI_KEY))
    index_name = os.getenv("MEILISEARCH_COMPANY_INDEX", DEFAULT_COMPANY_INDEX)
    index = client.index(index_name)
    try:
        index.delete_all_documents()
    except Exception:
        pass
    index.update_searchable_attributes(["corp_name", "stock_code", "corp_code"])
    index.update_filterable_attributes(["corp_cls", "stock_code"])
    task = index.add_documents(docs, primary_key="id")
    task_uid = getattr(task, "task_uid", None)
    if task_uid is None and isinstance(task, dict):
        task_uid = task.get("taskUid")
    print(f"indexed={len(docs)}")
    print(f"index_name={index_name}")
    print(f"task_uid={task_uid}")
    print(f"cache_path={CACHE_PATH}")


if __name__ == "__main__":
    main()
