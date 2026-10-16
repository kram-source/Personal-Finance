"""HTTP routes for this feature. Business logic lives in src.services."""
from fastapi import APIRouter, HTTPException, Query, Request
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import text
from src.api.dependencies import *  # shared dependencies and service adapters
from src.api.schemas import *  # request/response models
from src.api.dependencies import _effective_user_id, _predict

router = APIRouter()

@router.post("/ai/predict-spending", response_model=PredictResponse, tags=["NestJS integration"], summary="Predict Future Spending", description="Forecasts next-month spending from the authenticated user's historical expenses. Read-only; months controls the history window.")

# Purpose: Internal NestJS-to-FastAPI endpoint for spending forecasts.
def ai_predict_spending(req: PredictRequest, request: Request):

    user_id = _effective_user_id(request, req.user_id)

    return _predict(user_id, req.months, req.as_of)

@router.get("/predict", response_model=PredictResponse, tags=["Task-list routes"], summary="Forecast Spending", description="Predicts next-month spending by category using the selected number of completed historical months.")

# Purpose: Public authenticated endpoint returning the next-month forecast.
def predict(

    request: Request,

    user_id: Optional[str] = Query(None),

    months: int = Query(3, ge=1, le=12),

    as_of: Optional[date] = Query(None),

):

    return _predict(_effective_user_id(request, user_id), months, as_of)

