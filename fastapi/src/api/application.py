"""FastAPI application factory and router registration."""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from sqlalchemy.exc import OperationalError
import jwt
from src.core.config import APP_TITLE, APP_VERSION, JWT_SECRET, FASTAPI_INTERNAL_API_KEY
from src.core.security import decode_access_token

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title=APP_TITLE, version=APP_VERSION, docs_url=None)
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json"}

@app.middleware("http")
async def require_nestjs_login(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_PATHS:
        return await call_next(request)
    if path.startswith("/ai/"):
        supplied_key = request.headers.get("x-internal-api-key", "")
        if FASTAPI_INTERNAL_API_KEY and supplied_key and supplied_key == FASTAPI_INTERNAL_API_KEY:
            return await call_next(request)
    auth = request.headers.get("authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return JSONResponse(status_code=401, content={"detail": "Sign in through NestJS and provide its access token as a Bearer token."}, headers={"WWW-Authenticate": "Bearer"})
    if not JWT_SECRET:
        logger.error("JWT_SECRET is not configured for FastAPI")
        return JSONResponse(status_code=503, content={"detail": "Authentication is not configured. Set JWT_SECRET to the same value as NestJS."})
    try:
        user_id = decode_access_token(token)
    except jwt.PyJWTError:
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired NestJS access token."}, headers={"WWW-Authenticate": "Bearer"})
    except RuntimeError:
        return JSONResponse(status_code=503, content={"detail": "Authentication is not configured. Set JWT_SECRET to the same value as NestJS."})
    query_user = request.query_params.get("user_id") or request.query_params.get("userId")
    if query_user and query_user != user_id:
        return JSONResponse(status_code=403, content={"detail": "You can only access analytics for the authenticated user."})
    if request.method in {"POST", "PUT", "PATCH"} and "application/json" in request.headers.get("content-type", ""):
        body = await request.body()
        if body:
            try:
                import json
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    body_user = parsed.get("userId", parsed.get("user_id"))
                    if body_user and body_user != user_id:
                        return JSONResponse(status_code=403, content={"detail": "You can only access analytics for the authenticated user."})
            except (ValueError, TypeError):
                pass
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive
    request.state.user_id = user_id
    return await call_next(request)

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    swagger_html = get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{app.title} - Swagger UI")
    html = swagger_html.body.decode().replace("</head>", "<style>.swagger-ui .topbar { display: none; }</style></head>", 1)
    return HTMLResponse(content=html)

@app.exception_handler(OperationalError)
def database_unavailable(_request, exc: OperationalError):
    logger.error("Database error: %s", exc.orig or exc)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT", "description": "Sign in through NestJS POST /auth/login and paste accessToken here."}
    paths = schema.get("paths", {})
    preferred = ["/auth/user-id", "/auth/account-data"]
    schema["paths"] = {**{p: paths[p] for p in preferred if p in paths}, **{p: v for p, v in paths.items() if p not in preferred}}
    for path, methods in schema.get("paths", {}).items():
        for operation in methods.values():
            if isinstance(operation, dict) and "responses" in operation and path not in PUBLIC_PATHS:
                operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema
app.openapi = custom_openapi

from src.api.routes import health, account, categorization, analytics, predictions, anomalies, duplicates
app.include_router(health.router)
app.include_router(account.router)
app.include_router(categorization.router)
app.include_router(analytics.router)
app.include_router(predictions.router)
app.include_router(anomalies.router)
app.include_router(duplicates.router)
