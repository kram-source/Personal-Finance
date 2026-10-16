"""HTTP routes for this feature. Business logic lives in src.services."""
from fastapi import APIRouter, HTTPException, Query, Request
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import text
from src.api.dependencies import *  # shared dependencies and service adapters
from src.api.schemas import *  # request/response models
from src.api.dependencies import _effective_user_id, _categorize

router = APIRouter()

@router.post("/ai/categorize-transaction", response_model=CategorizeResponse, tags=["NestJS integration"], summary="Categorize a Transaction", description="Suggests a transaction category from its description and optional merchant. Internal NestJS calls may provide userId with the internal API key; direct Swagger calls require a Bearer token.")

# Purpose: Internal NestJS-to-FastAPI endpoint for transaction category suggestions.
def ai_categorize(req: CategorizeRequest, request: Request):

    req.user_id = _effective_user_id(request, req.user_id)

    return _categorize(req)

@router.post("/categorize", response_model=CategorizeResponse, tags=["Task-list routes"], summary="Categorize a Transaction", description="Suggests a category from a transaction description and optional merchant. The authenticated user ID is taken from the Bearer token.")

# Purpose: Public authenticated endpoint for a category suggestion.
def categorize(req: CategorizeRequest, request: Request):

    req.user_id = _effective_user_id(request, req.user_id)

    return _categorize(req)

