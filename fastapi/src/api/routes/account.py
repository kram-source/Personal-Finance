"""HTTP routes for this feature. Business logic lives in src.services."""
from fastapi import APIRouter, HTTPException, Query, Request
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import text
from src.api.dependencies import *  # shared dependencies and service adapters
from src.api.schemas import *  # request/response models

router = APIRouter()

@router.get(
    "/auth/user-id",
    tags=["Authorization & Data Observation"],
    operation_id="get_authenticated_user_id",
    summary="Get My User ID",
    description=(
        "Returns the user ID (UUID) from your authenticated NestJS access token. "
        "Click Authorize and use a valid Bearer access token first. Copy the returned "
        "userId when manually testing endpoints that accept an explicit userId. "
        "This endpoint does not create a user or modify data."
    ),
)
def get_authenticated_user_id(request: Request):
    """Return the authenticated user's ID for use with other FastAPI endpoints."""
    return {
        "userId": request.state.user_id,
        "message": "Use this userId when testing FastAPI requests. It belongs to the authenticated account.",
    }

@router.get(
    "/auth/account-data",
    tags=["Authorization & Data Observation"],
    operation_id="get_my_account_data_for_testing",
    summary="Get My Account Data & Test Examples",
    description=(
        "Returns the authenticated account profile and its available transactions, categories, "
        "and budgets from the shared NestJS/Prisma PostgreSQL database, plus copy-ready example "
        "parameters/payloads for testing the analytics endpoints. This is read-only and only "
        "returns records belonging to the signed-in user (plus global categories). Authorize "
        "with a NestJS Bearer access token first. Large accounts may return a large response."
    ),
)
def get_my_account_data_for_testing(request: Request):
    """Return the signed-in user's available data and examples for trying the API."""
    user_id = request.state.user_id

    with engine.connect() as conn:
        user = conn.execute(
            text('SELECT id, name, email FROM "User" WHERE id = :uid'),
            {"uid": user_id},
        ).mappings().first()
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Authenticated user was not found in the shared database. Sign in with a NestJS account present in this database.",
            )

        transactions = conn.execute(text("""
            SELECT t.id, t.description, t.amount, t.type, t.date, t.source,
                   t."categoryId" AS "categoryId", c.name AS category
            FROM "Transaction" t
            LEFT JOIN "Category" c ON c.id = t."categoryId"
            WHERE t."userId" = :uid
            ORDER BY t.date DESC, t."createdAt" DESC
        """), {"uid": user_id}).mappings().all()

        categories = conn.execute(text("""
            SELECT id, name, type, "userId" AS "userId"
            FROM "Category"
            WHERE "userId" IS NULL OR "userId" = :uid
            ORDER BY type, name
        """), {"uid": user_id}).mappings().all()

        budgets = conn.execute(text("""
            SELECT b.id, b.amount, b.year, b.month, b."categoryId" AS "categoryId",
                   c.name AS category
            FROM "Budget" b
            LEFT JOIN "Category" c ON c.id = b."categoryId"
            WHERE b."userId" = :uid
            ORDER BY b.year DESC, b.month DESC, c.name
        """), {"uid": user_id}).mappings().all()

    # Purpose: Convert database/date/decimal values into values that JSON can serialize.
    def json_safe(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    # Purpose: Normalize database result rows before sending them in API responses.
    def clean_rows(rows):
        return [{key: json_safe(value) for key, value in dict(row).items()} for row in rows]

    transaction_data = clean_rows(transactions)
    category_data = clean_rows(categories)
    budget_data = clean_rows(budgets)

    first_expense = next((row for row in transaction_data if row.get("type") == "EXPENSE"), None)
    first_transaction = transaction_data[0] if transaction_data else None
    example_description = (first_expense or first_transaction or {}).get("description", "Coffee shop purchase")
    example_type = (first_expense or first_transaction or {}).get("type", "EXPENSE")
    if example_type not in ("EXPENSE", "INCOME"):
        example_type = "EXPENSE"

    return {
        "readOnly": True,
        "account": {
            "userId": str(user["id"]),
            "name": user["name"],
            "email": user["email"],
        },
        "counts": {
            "transactions": len(transaction_data),
            "categories": len(category_data),
            "budgets": len(budget_data),
        },
        "transactions": transaction_data,
        "categories": category_data,
        "budgets": budget_data,
        "testExamples": {
            "GET /anomalies": {"user_id": str(user["id"]), "multiplier": 2.0},
            "GET /predict": {"user_id": str(user["id"]), "months": 3},
            "GET /duplicates": {"user_id": str(user["id"]), "window_days": 3},
            "GET /analytics/insights": {"user_id": str(user["id"])},
            "GET /analytics/summary": {"user_id": str(user["id"]), "months": 3, "multiplier": 2.0},
            "POST /categorize": {
                "description": example_description,
                "merchant": None,
                "type": example_type,
                "userId": str(user["id"]),
            },
            "POST /ai/categorize-transaction": {
                "description": example_description,
                "merchant": None,
                "type": example_type,
                "userId": str(user["id"]),
            },
            "POST /ai/detect-anomaly": {"userId": str(user["id"]), "multiplier": 2.0},
            "POST /ai/predict-spending": {"userId": str(user["id"]), "months": 3},
        },
        "notes": [
            "All returned records are read-only and were not modified.",
            "Transactions and budgets belong to the authenticated account; categories include its own and shared global categories.",
            "Use the testExamples values to populate the corresponding Swagger requests.",
            "If there are no transactions yet, create them through NestJS before testing transaction analytics.",
        ],
    }

