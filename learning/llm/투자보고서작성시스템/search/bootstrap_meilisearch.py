from __future__ import annotations

import os
import re
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from meilisearch import Client


def _load_env() -> None:
    current = Path(__file__).resolve()
    for candidate in (
        current.parents[2] / ".env",
        current.parents[1] / ".env",
        current.parents[3] / ".env",
    ):
        if candidate.exists():
            load_dotenv(candidate, override=False)


def _download_nasdaq_list() -> list[dict[str, str]]:
    url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    frame = pd.read_csv(
        StringIO(response.text),
        sep="|",
        dtype=str,
    )
    frame = frame[frame["Symbol"].notna()]
    frame = frame[frame["Symbol"] != "File Creation Time"]
    normalized = (
        frame.rename(columns={"Symbol": "symbol", "Security Name": "name"})
        .assign(exchange="NASDAQ")
        .loc[:, ["symbol", "name", "exchange"]]
        .fillna("")
        .reset_index(drop=True)
    )
    normalized["id"] = [
        f"{idx}_{re.sub(r'[^0-9A-Za-z_-]', '_', symbol)}"
        for idx, symbol in enumerate(normalized["symbol"], start=1)
    ]
    documents = normalized.loc[:, ["id", "symbol", "name", "exchange"]].to_dict(orient="records")
    return documents


def main() -> None:
    _load_env()
    url = os.getenv("MEILISEARCH_URL", "http://127.0.0.1:7700")
    master_key = os.getenv("MEILISEARCH_MASTER_KEY")
    index_name = os.getenv("MEILISEARCH_INDEX", "nasdaq")

    client = Client(url, master_key)
    documents = _download_nasdaq_list()

    index = client.index(index_name)
    try:
        index.delete_all_documents()
    except Exception:
        pass
    index.update_filterable_attributes(["symbol", "name", "exchange"])
    task = index.add_documents(documents, primary_key="id")

    print(f"indexed={len(documents)}")
    task_uid = getattr(task, "task_uid", None)
    if task_uid is None and isinstance(task, dict):
        task_uid = task.get("taskUid")
    print(f"task_uid={task_uid}")
    print(f"index_name={index_name}")


if __name__ == "__main__":
    main()
