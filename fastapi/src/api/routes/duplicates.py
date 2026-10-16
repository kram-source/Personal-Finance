"""HTTP routes for this feature. Business logic lives in src.services."""
from fastapi import APIRouter, HTTPException, Query, Request
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import text
from src.api.dependencies import *  # shared dependencies and service adapters
from src.api.schemas import *  # request/response models
from src.api.dependencies import _effective_user_id, _duplicates

router = APIRouter()

@router.get("/duplicates", response_model=DuplicateResponse, tags=["Analytics"], summary="Find Possible Duplicate Transactions", description="Identifies similar transactions within the requested day window. This is advisory only and never deletes or changes records.")

def duplicates(

    request: Request,

    user_id: Optional[str] = Query(None),

    window_days: int = Query(3, ge=0, le=30),

):

    """Find likely duplicate expenses; never deletes or changes transactions."""

    return _duplicates(_effective_user_id(request, user_id), window_days)

