from __future__ import annotations

from .prediction import first_of_month, add_months, months_between

import re
from collections import defaultdict
from statistics import median
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping, NamedTuple, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

def spending_insights(expenses: list[Expense], as_of: date) -> dict:
    """Compare month-to-date spending with the same elapsed period last month."""
    from calendar import monthrange

    current_start = first_of_month(as_of)
    previous_start = add_months(current_start, -1)
    previous_end_day = min(as_of.day, monthrange(previous_start.year, previous_start.month)[1])
    previous_end = date(previous_start.year, previous_start.month, previous_end_day)

    current: dict[str, float] = defaultdict(float)
    previous: dict[str, float] = defaultdict(float)
    names: dict[str, str] = {}
    for item in expenses:
        names[item.category_id] = item.category
        if current_start <= item.date <= as_of:
            current[item.category_id] += item.amount
        elif previous_start <= item.date <= previous_end:
            previous[item.category_id] += item.amount

    current_total = round(sum(current.values()), 2)
    previous_total = round(sum(previous.values()), 2)
    change = None if previous_total == 0 else round((current_total - previous_total) / previous_total * 100, 1)
    category_ids = set(current) | set(previous)
    category_changes = []
    for cid in category_ids:
        now = current.get(cid, 0.0)
        before = previous.get(cid, 0.0)
        category_changes.append({
            "categoryId": cid,
            "category": names.get(cid, "Other"),
            "currentAmount": round(now, 2),
            "previousAmount": round(before, 2),
            "changeAmount": round(now - before, 2),
            "changePercent": None if before == 0 else round((now - before) / before * 100, 1),
        })
    category_changes.sort(key=lambda row: row["currentAmount"], reverse=True)
    largest_increase = sorted(category_changes, key=lambda row: row["changeAmount"], reverse=True)
    return {
        "asOf": as_of.isoformat(),
        "period": {"currentStart": current_start.isoformat(), "currentEnd": as_of.isoformat(),
                   "previousStart": previous_start.isoformat(), "previousEnd": previous_end.isoformat()},
        "currentPeriodSpend": current_total,
        "previousPeriodSpend": previous_total,
        "changePercent": change,
        "topCategories": category_changes[:5],
        "largestIncrease": largest_increase[0] if largest_increase and largest_increase[0]["changeAmount"] > 0 else None,
        "notes": ([f"Spending is {abs(change):.1f}% {'higher' if change > 0 else 'lower'} than the comparable period last month."]
                  if change is not None and change != 0 else
                  ["There is no previous-period spending baseline yet."] if previous_total == 0 else
                  ["Spending is unchanged from the comparable period last month."]),
    }

