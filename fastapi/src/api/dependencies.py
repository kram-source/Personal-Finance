"""Shared API dependencies and read-only database/service adapters.

Route modules import from here rather than importing the application module,
which avoids circular imports during app startup.
"""
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, Request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import core
from src.core.config import DATABASE_URL
from src.api.schemas import *  # shared schema types used by feature adapters

logger = logging.getLogger("uvicorn.error")
engine = create_engine(core.normalize_database_url(DATABASE_URL), pool_pre_ping=True)

def _load_expenses(user_id: str) -> list[core.Expense]:

    with engine.connect() as conn:

        if conn.execute(text(core.SQL_USER_EXISTS), {"id": user_id}).first() is None:

            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        rows = conn.execute(text(core.SQL_USER_EXPENSES), {"uid": user_id}).mappings().all()

    return core.rows_to_expenses(rows)





def _load_budgets(user_id: str, year: int, month: int) -> list[dict]:

    """Read budgets for a forecast month from the Prisma Budget table."""

    query = text('''

        SELECT b.amount AS "budget_amount", b."categoryId" AS "category_id",

               c.name AS "category"

        FROM "Budget" b

        JOIN "Category" c ON c.id = b."categoryId"

        WHERE b."userId" = :uid AND b.year = :year AND b.month = :month

    ''')

    with engine.connect() as conn:

        rows = conn.execute(query, {"uid": user_id, "year": year, "month": month}).mappings().all()

    return [dict(row) for row in rows]





# Purpose: Run rule-based categorization and optionally resolve the matching shared/user category ID.
def _categorize(req: CategorizeRequest) -> CategorizeResponse:

    combined_description = " ".join(part.strip() for part in (req.merchant, req.description) if part and part.strip())

    result = core.categorize_text(combined_description, req.type)

    category_id = None

    if req.user_id:

        with engine.connect() as conn:

            row = conn.execute(

                text(core.SQL_FIND_CATEGORY),

                {"name": result.category, "type": req.type, "uid": req.user_id},

            ).first()

        category_id = str(row[0]) if row else None

    return CategorizeResponse(

        description=req.description,

        type=req.type,

        category=result.category,

        category_id=category_id,

        matched_keyword=result.matched_keyword,

        confidence=0.90 if result.matched_keyword else 0.35,

    )





# Purpose: Load a user’s expenses and return transactions that are unusually large for their category.
def _anomalies(user_id: str, multiplier: float) -> AnomalyResponse:

    found = core.find_anomalies(_load_expenses(user_id), multiplier)

    return AnomalyResponse(

        user_id=user_id,

        multiplier=multiplier,

        anomalies=[

            AnomalyItem(

                transaction_id=a.expense.id,

                description=a.expense.description,

                category=a.expense.category,

                category_id=a.expense.category_id,

                amount=a.expense.amount,

                date=a.expense.date,

                category_average=a.category_average,

                times_average=a.times_average,

                severity=a.severity,

                reason=a.reason,

            )

            for a in found

        ],

    )





# Purpose: Calculate a next-month spending forecast from completed months of expense history.
def _predict(user_id: str, months: int, as_of: Optional[date]) -> PredictResponse:

    expenses = _load_expenses(user_id)

    p = core.predict_next_month(expenses, as_of or datetime.now(timezone.utc).date(), months)

    return PredictResponse(

        user_id=user_id,

        year=p.year,

        month=p.month,

        total_predicted=p.total,

        based_on=PredictionBasis(start=p.based_on_start, end=p.based_on_end, months=p.months_used),

        predictions=[

            PredictionItem(category=c.category, category_id=c.category_id, predicted_amount=c.predicted_amount)

            for c in p.categories

        ],

    )





# Purpose: Find likely duplicate expenses for manual review; this function never deletes records.
def _duplicates(user_id: str, window_days: int) -> DuplicateResponse:

    found = core.find_duplicate_transactions(_load_expenses(user_id), window_days)

    return DuplicateResponse(

        user_id=user_id,

        window_days=window_days,

        count=len(found),

        duplicates=[DuplicateItem(

            first_transaction_id=p.first.id,

            second_transaction_id=p.second.id,

            first_description=p.first.description,

            second_description=p.second.description,

            amount=p.first.amount,

            first_date=p.first.date,

            second_date=p.second.date,

            days_apart=p.days_apart,

            reason=p.reason,

        ) for p in found],

    )





def _effective_user_id(request: Request, supplied_user_id: Optional[str] = None) -> str:

    """Use the authenticated JWT identity; allow explicit IDs only for internal calls.



    Middleware validates supplied IDs against the JWT on public requests. The

    internal API-key path intentionally bypasses JWT and must therefore provide

    userId in its NestJS payload.

    """

    authenticated_user_id = getattr(request.state, "user_id", None)

    if authenticated_user_id:

        if supplied_user_id and supplied_user_id != authenticated_user_id:

            raise HTTPException(status_code=403, detail="You can only access analytics for the authenticated user.")

        return authenticated_user_id

    if supplied_user_id:

        return supplied_user_id

    raise HTTPException(status_code=401, detail="A valid Bearer token is required, or a trusted NestJS internal request must include userId.")





# --------------------------------------------------------------------------------

