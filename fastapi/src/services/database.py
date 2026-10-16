from __future__ import annotations

import re
from collections import defaultdict
from statistics import median
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping, NamedTuple, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PRISMA_ONLY_PARAMS = {
    "schema",
    "connection_limit",
    "pool_timeout",
    "pgbouncer",
    "socket_timeout",
    "statement_cache_size",
}


def normalize_database_url(url: str) -> str:
    """
    Accept the very same DATABASE_URL the NestJS app uses, e.g.
        postgresql://user:pass@localhost:5432/personal_finance?schema=public
    and turn it into something SQLAlchemy + psycopg understand.
    """
    url = url.strip().strip("\"'")
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme not in ("postgres", "postgresql") and not scheme.startswith("postgresql+"):
        # Preserve non-PostgreSQL URLs verbatim (useful for isolated SQLite tests).
        return url
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+psycopg"
    query = urlencode(
        [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k not in PRISMA_ONLY_PARAMS
        ]
    )
    return urlunsplit((scheme, parts.netloc, parts.path, query, parts.fragment))


SQL_USER_EXISTS = 'SELECT 1 FROM "User" WHERE id = :id'


SQL_USER_EXPENSES = """
SELECT t.id          AS "id",
       t.description AS "description",
       t.amount      AS "amount",
       t."date"      AS "date",
       c.id          AS "category_id",
       c.name        AS "category"
FROM "Transaction" t
JOIN "Category" c ON c.id = t."categoryId"
WHERE t."userId" = :uid
  AND t."type" = 'EXPENSE'
"""


SQL_FIND_CATEGORY = """
SELECT c.id AS "id"
FROM "Category" c
WHERE LOWER(c.name) = LOWER(:name)
  AND CAST(c."type" AS TEXT) = :type
  AND (c."userId" IS NULL OR c."userId" = :uid)
ORDER BY (c."userId" IS NULL)
LIMIT 1
"""

