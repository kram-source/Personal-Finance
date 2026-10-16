"""Application entry point. Run: uvicorn main:app --reload"""
from src.api.application import app

__all__ = ["app"]
