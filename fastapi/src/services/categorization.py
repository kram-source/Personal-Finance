from __future__ import annotations

import re
from collections import defaultdict
from statistics import median
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping, NamedTuple, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CATEGORY_RULES: dict[str, list[tuple[str, list[str]]]] = {
    "EXPENSE": [
        ("Healthcare", [
            "pharmacy", "medicine", "medical", "doctor", "dentist", "dental",
            "hospital", "clinic", "prescription", "checkup", "check up",
            "optician", "physio", "diagnostic", "lab test",
        ]),
        ("Entertainment", [
            "movie", "cinema", "concert", "streaming", "netflix", "spotify",
            "hotstar", "prime video", "theatre", "theater", "game", "gaming",
            "amusement",
        ]),
        ("Bills", [
            "bill", "electricity", "electric", "internet", "broadband", "wifi",
            "rent", "utility", "utilities", "insurance", "premium", "loan",
            "emi", "phone recharge", "mobile recharge", "prepaid", "postpaid",
        ]),
        ("Transport", [
            "uber", "ola", "lyft", "taxi", "cab", "rideshare", "ride share",
            "bus", "train", "metro", "subway", "railway", "irctc", "fuel",
            "petrol", "diesel", "parking", "toll", "flight", "airline",
            "airfare", "ferry", "rickshaw", "commute",
        ]),
        ("Food", [
            "grocery", "groceries", "supermarket", "market", "vegetable",
            "fruit", "cafe", "coffee", "tea", "restaurant", "lunch", "dinner",
            "breakfast", "pizza", "burger", "swiggy", "zomato", "bakery",
            "takeout", "takeaway", "meal", "snack", "catering", "canteen",
            "dining", "food",
        ]),
        ("Shopping", [
            "amazon", "flipkart", "myntra", "mall", "shopping", "purchase",
            "clothes", "clothing", "shoe", "supplies", "household",
            "home goods", "goods", "storage", "furniture", "electronics",
            "gadget", "book",
        ]),
    ],
    "INCOME": [
        ("Salary", ["salary", "payroll", "wage", "paycheck", "paycheque", "stipend"]),
        ("Freelance", [
            "freelance", "freelancer", "consulting", "consultant", "invoice",
            "client", "gig", "commission",
        ]),
    ],
}


DEFAULT_CATEGORY = "Other"


def _compile(keyword: str) -> re.Pattern:
    # whole-word match, allowing a plural: "bus" matches "buses", not "business"
    return re.compile(r"\b" + re.escape(keyword) + r"(?:s|es)?\b")


_COMPILED = {
    kind: [(name, [(kw, _compile(kw)) for kw in kws]) for name, kws in rules]
    for kind, rules in CATEGORY_RULES.items()
}


class Categorization(NamedTuple):
    category: str
    matched_keyword: Optional[str]


def categorize_text(description: str, type_: str = "EXPENSE") -> Categorization:
    """Return the category name for a transaction description (keyword rules)."""
    text = (description or "").lower()
    for name, keywords in _COMPILED.get(type_, _COMPILED["EXPENSE"]):
        for kw, pattern in keywords:
            if pattern.search(text):
                return Categorization(name, kw)
    return Categorization(DEFAULT_CATEGORY, None)

