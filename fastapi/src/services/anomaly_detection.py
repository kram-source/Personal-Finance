from __future__ import annotations

import re
from collections import defaultdict
from statistics import median
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping, NamedTuple, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

@dataclass(frozen=True)
# Purpose: Define the Anomaly data/model type.
class Anomaly:
    expense: Expense
    category_average: float
    times_average: float
    severity: str
    reason: str


def find_anomalies(expenses: list[Expense], multiplier: float = 2.0) -> list[Anomaly]:
    """Flag unusually large expenses using the median of peer transactions.

    The median is more resistant than the mean to a few very large payments. A
    transaction is compared with *other* transactions in the same category, so it
    cannot inflate its own baseline. The API retains the legacy categoryAverage
    field name for backwards compatibility; it now represents this robust baseline.
    """
    by_category: dict[str, list[Expense]] = defaultdict(list)
    for e in expenses:
        if e.amount > 0:
            by_category[e.category_id].append(e)

    found: list[Anomaly] = []
    for items in by_category.values():
        if len(items) < 2:
            continue
        for item in items:
            peers = [peer.amount for peer in items if peer.id != item.id]
            if not peers:
                continue
            baseline = float(median(peers))
            if baseline <= 0:
                continue
            ratio = item.amount / baseline
            if item.amount > multiplier * baseline:
                severity = "high" if ratio >= 4 else "medium" if ratio >= 3 else "low"
                reason = (
                    f"This {item.category.lower()} expense is {ratio:.1f}x the average baseline "
                    f"(median of other {item.category.lower()} transactions)."
                )
                found.append(Anomaly(item, round(baseline, 2), round(ratio, 2), severity, reason))
    found.sort(key=lambda a: a.times_average, reverse=True)
    return found

