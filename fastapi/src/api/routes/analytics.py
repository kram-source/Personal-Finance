"""HTTP routes for this feature. Business logic lives in src.services."""
from fastapi import APIRouter, HTTPException, Query, Request
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import text
from src.api.dependencies import *  # shared dependencies and service adapters
from src.api.schemas import *  # request/response models
from src.api.dependencies import _effective_user_id, _predict, _anomalies, _load_budgets, _duplicates, _load_expenses

router = APIRouter()

@router.get("/analytics/summary", tags=["Analytics"], summary="Get Analytics Dashboard Summary", description="Combines spending forecast, budget comparison, anomalies, duplicate candidates, and spending insights for the authenticated user.")

# Purpose: Combine forecast, budget comparison, anomalies, duplicates, and insights into one response.
def analytics_summary(

    request: Request,

    user_id: Optional[str] = Query(None),

    months: int = Query(3, ge=1, le=12),

    multiplier: float = Query(2.0, gt=1),

    as_of: Optional[date] = Query(None),

):

    user_id = _effective_user_id(request, user_id)

    """Return a single dashboard payload containing forecast and anomaly analysis."""

    forecast = _predict(user_id, months, as_of)

    anomaly_result = _anomalies(user_id, multiplier)

    budgets = _load_budgets(user_id, forecast.year, forecast.month)

    duplicate_result = _duplicates(user_id, 3)

    insights = core.spending_insights(_load_expenses(user_id), as_of or datetime.now(timezone.utc).date())

    predicted_by_category = {p.category_id: p.predicted_amount for p in forecast.predictions}

    budget_comparison = []

    for budget in budgets:

        budget_amount = float(budget["budget_amount"])

        predicted_amount = predicted_by_category.get(str(budget["category_id"]), 0.0)

        variance = round(budget_amount - predicted_amount, 2)

        budget_comparison.append({

            "categoryId": str(budget["category_id"]),

            "category": budget["category"],

            "budgetAmount": round(budget_amount, 2),

            "predictedAmount": round(predicted_amount, 2),

            "remainingAmount": variance,

            "likelyToExceed": predicted_amount > budget_amount,

        })

    return {

        "userId": user_id,

        "forecast": forecast.model_dump(by_alias=True, mode="json"),

        "budgetComparison": budget_comparison,

        "budgetSummary": {

            "categoriesCompared": len(budget_comparison),

            "likelyToExceed": sum(item["likelyToExceed"] for item in budget_comparison),

        },

        "anomalySummary": {

            "count": len(anomaly_result.anomalies),

            "high": sum(a.severity == "high" for a in anomaly_result.anomalies),

            "medium": sum(a.severity == "medium" for a in anomaly_result.anomalies),

            "low": sum(a.severity == "low" for a in anomaly_result.anomalies),

        },

        "anomalies": [a.model_dump(by_alias=True, mode="json") for a in anomaly_result.anomalies],

        "duplicateSummary": {"count": duplicate_result.count, "windowDays": duplicate_result.window_days},

        "possibleDuplicates": [d.model_dump(by_alias=True, mode="json") for d in duplicate_result.duplicates],

        "insights": insights,

    }

@router.get("/analytics/insights", tags=["Analytics"], summary="Get Spending Insights", description="Returns month-to-date spending trends and category-level changes for the authenticated user.")

def analytics_insights(

    request: Request,

    user_id: Optional[str] = Query(None),

    as_of: Optional[date] = Query(None),

):

    """Return month-to-date spending trends and category-level changes."""

    user_id = _effective_user_id(request, user_id)

    expenses = _load_expenses(user_id)

    return {"userId": user_id, **core.spending_insights(expenses, as_of or datetime.now(timezone.utc).date())}

