from __future__ import annotations

import re
from collections import defaultdict
from statistics import median
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping, NamedTuple, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

@dataclass(frozen=True)
# Purpose: Define the DuplicatePair data/model type.
class DuplicatePair:
    first: Expense
    second: Expense
    days_apart: int
    reason: str


def _normalise_description(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def find_duplicate_transactions(expenses: list[Expense], window_days: int = 3) -> list[DuplicatePair]:
    """Find likely duplicates with equal amounts and near-identical descriptions.

    This is a review suggestion, not an automatic deletion: matching transactions
    can be legitimate recurring purchases. Dates must be within ``window_days``.
    """
    if window_days < 0:
        raise ValueError("window_days must be non-negative")
    candidates: dict[tuple[str, float], list[Expense]] = defaultdict(list)
    for item in expenses:
        if item.amount > 0:
            candidates[(_normalise_description(item.description), round(item.amount, 2))].append(item)

    pairs: list[DuplicatePair] = []
    for items in candidates.values():
        items.sort(key=lambda item: (item.date, item.id))
        for i, first in enumerate(items):
            for second in items[i + 1:]:
                days = (second.date - first.date).days
                if days > window_days:
                    break
                if first.id == second.id:
                    continue
                pairs.append(DuplicatePair(
                    first, second, days,
                    f"Same normalised description and amount within {days} day(s); review before removing either transaction.",
                ))
    pairs.sort(key=lambda pair: (pair.days_apart, -pair.first.amount, pair.first.date))
    return pairs

