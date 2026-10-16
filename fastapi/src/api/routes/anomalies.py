"""HTTP routes for this feature. Business logic lives in src.services."""
from fastapi import APIRouter, HTTPException, Query, Request
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import text
from src.api.dependencies import *  # shared dependencies and service adapters
from src.api.schemas import *  # request/response models
from src.api.dependencies import _effective_user_id, _anomalies

router = APIRouter()

@router.post("/ai/detect-anomaly", response_model=AnomalyResponse, tags=["NestJS integration"], summary="Detect Unusual Spending", description="Finds unusually large expenses for the authenticated user using the category average and supplied multiplier. Read-only; does not modify transactions.")

# Purpose: Internal NestJS-to-FastAPI endpoint for spending anomaly detection.
def ai_detect_anomaly(req: AnomalyRequest, request: Request):

    user_id = _effective_user_id(request, req.user_id)

    return _anomalies(user_id, req.multiplier)

@router.get("/anomalies", response_model=AnomalyResponse, tags=["Task-list routes"], summary="Find Spending Anomalies", description="Returns expenses that exceed the category average multiplied by multiplier. Uses the signed-in user's transactions.")

# Purpose: Public authenticated endpoint listing unusual expenses.
def anomalies(request: Request, user_id: Optional[str] = Query(None), multiplier: float = Query(2.0, gt=1)):

    return _anomalies(_effective_user_id(request, user_id), multiplier)

