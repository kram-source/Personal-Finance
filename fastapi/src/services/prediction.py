from __future__ import annotations

import re
from collections import defaultdict
from statistics import median
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping, NamedTuple, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

def first_of_month(d: date) -> date:
    return d.replace(day=1)


def add_months(d: date, n: int) -> date:
    """First day of the month that is n months after d's month (n may be negative)."""
    total = d.year * 12 + (d.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)


def months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


@dataclass(frozen=True)
# Purpose: Define the CategoryPrediction data/model type.
class CategoryPrediction:
    category_id: str
    category: str
    predicted_amount: float


@dataclass(frozen=True)
# Purpose: Define the Prediction data/model type.
class Prediction:
    year: int                 # month being predicted (the month after the window)
    month: int
    based_on_start: date      # first day of the data actually used
    based_on_end: date        # last day of the data actually used (inclusive)
    months_used: int
    total: float
    categories: list[CategoryPrediction]


def predict_next_month(
    expenses: list[Expense], as_of: date, months: int = 3
) -> Prediction:
    """
    Average monthly spend per category over the last `months` COMPLETED calendar
    months before `as_of`. The result is the estimate for the month right after
    that window (the current month if as_of is mid-month).

    If the user has less history than `months`, only the months since their first
    expense are used, so a new user is not under-estimated.
    """
    this_month = first_of_month(as_of)
    window_start = add_months(this_month, -months)
    empty = Prediction(
        this_month.year, this_month.month, window_start,
        this_month - timedelta(days=1), 0, 0.0, [],
    )
    if not expenses:
        return empty

    first_month = first_of_month(min(e.date for e in expenses))
    start = max(window_start, first_month)
    months_used = months_between(start, this_month)
    if months_used <= 0:
        return empty

    totals: dict[str, float] = defaultdict(float)
    names: dict[str, str] = {}
    for e in expenses:
        if start <= e.date < this_month:
            totals[e.category_id] += e.amount
            names[e.category_id] = e.category

    categories = sorted(
        (
            CategoryPrediction(cid, names[cid], round(total / months_used, 2))
            for cid, total in totals.items()
        ),
        key=lambda p: (-p.predicted_amount, p.category),
    )
    return Prediction(
        this_month.year, this_month.month, start,
        this_month - timedelta(days=1), months_used,
        round(sum(p.predicted_amount for p in categories), 2), categories,
    )

