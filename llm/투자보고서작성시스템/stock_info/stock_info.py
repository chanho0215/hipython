from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv


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


def _safe_pick(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in source and source[key] not in (None, ""):
            return source[key]
    return "N/A"


def _format_value(value: Any) -> Any:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        if abs(value) >= 1_000:
            return f"{value:,.0f}"
        return round(value, 4)
    return value


def _format_columns(frame: pd.DataFrame) -> pd.DataFrame:
    formatted = frame.copy()
    formatted.columns = [
        column.strftime("%Y-%m-%d") if hasattr(column, "strftime") else str(column)
        for column in formatted.columns
    ]
    return formatted


@dataclass
class Stock:
    symbol: str

    def __post_init__(self) -> None:
        self.symbol = self.symbol.upper().strip()
        self.ticker = yf.Ticker(self.symbol)

    def _info(self) -> dict[str, Any]:
        return self.ticker.info or {}

    def get_basic_info_frame(self) -> pd.DataFrame:
        info = self._info()
        basic_rows = [
            ("symbol", self.symbol),
            ("longName", _safe_pick(info, "longName", "shortName")),
            ("industry", _safe_pick(info, "industry")),
            ("sector", _safe_pick(info, "sector")),
            ("marketCap", _format_value(_safe_pick(info, "marketCap"))),
            ("sharesOutstanding", _format_value(_safe_pick(info, "sharesOutstanding"))),
            ("currentPrice", _format_value(_safe_pick(info, "currentPrice", "regularMarketPrice"))),
            ("trailingPE", _format_value(_safe_pick(info, "trailingPE"))),
            ("fiftyTwoWeekHigh", _format_value(_safe_pick(info, "fiftyTwoWeekHigh"))),
            ("fiftyTwoWeekLow", _format_value(_safe_pick(info, "fiftyTwoWeekLow"))),
        ]
        return pd.DataFrame(basic_rows, columns=["항목", "Value"])

    def get_basic_info(self) -> str:
        return self.get_basic_info_frame().to_markdown(index=False)

    def _select_rows(
        self,
        frame: pd.DataFrame | None,
        labels: list[str],
    ) -> pd.DataFrame:
        if frame is None or frame.empty:
            return pd.DataFrame(columns=["데이터 없음"])

        available = [label for label in labels if label in frame.index]
        if not available:
            return pd.DataFrame(columns=["데이터 없음"])

        selected = frame.loc[available].copy()
        selected.index.name = "항목"
        return _format_columns(selected)

    def get_financial_statement_frames(self) -> dict[str, pd.DataFrame]:
        income = self._select_rows(
            self.ticker.quarterly_income_stmt,
            ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"],
        )
        balance = self._select_rows(
            self.ticker.quarterly_balance_sheet,
            ["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity"],
        )
        cash_flow = self._select_rows(
            self.ticker.quarterly_cashflow,
            ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow"],
        )
        return {
            "Quarterly Income Statement": income,
            "Quarterly Balance Sheet": balance,
            "Quarterly Cash Flow": cash_flow,
        }

    def get_financial_statement(self) -> str:
        sections = []
        for title, frame in self.get_financial_statement_frames().items():
            sections.append(f"### {title}\n{frame.to_markdown()}")
        return "\n\n".join(sections)
