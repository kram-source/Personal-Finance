from __future__ import annotations

import re
from collections import defaultdict
from statistics import median
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping, NamedTuple, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

@dataclass(frozen=True)
# Purpose: Define the Expense data/model type.
class Expense:
    id: str
    description: str
    amount: float
    date: date
    category_id: str
    category: str


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def rows_to_expenses(rows: Iterable[Mapping]) -> list[Expense]:
    return [
        Expense(
            id=str(r["id"]),
            description=r["description"],
            amount=float(r["amount"]),
            date=_as_date(r["date"]),
            category_id=str(r["category_id"]),
            category=r["category"],
        )
        for r in rows
    ]

