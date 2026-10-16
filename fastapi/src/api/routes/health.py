"""HTTP routes for this feature. Business logic lives in src.services."""
from fastapi import APIRouter, HTTPException, Query, Request
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import text
from src.api.dependencies import *  # shared dependencies and service adapters
from src.api.schemas import *  # request/response models

router = APIRouter()

@router.get("/health", tags=["Health"], summary="Check API and Database Health", description="Checks whether FastAPI can connect to PostgreSQL. Does not return account data.")

def health():

    """Handy for checking that NestJS can reach FastAPI and FastAPI can reach the database."""

    with engine.connect() as conn:

        conn.execute(text("SELECT 1"))

    return {"status": "ok", "database": "ok"}

