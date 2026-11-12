import logging
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.collections import (
    router as collections_router,
)
from app.api.routes.conversations import (
    router as conversations_router,
)
from app.api.routes.documents import router as documents_router
from app.api.routes.users import router as users_router
from app.core.config import settings
from app.core.logging import configure_logging, request_id_var
from app.db.session import engine
from app.services.document_service import check_storage_ready

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

configure_logging(settings.log_level, settings.log_format)
logger = logging.getLogger("enterprise_rag.api")


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    # Accept a caller-supplied ID only if it is short and printable.
    supplied = request.headers.get("X-Request-ID", "")
    request_id = supplied if supplied.isprintable() and 0 < len(supplied) <= 64 else uuid4().hex
    token = request_id_var.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra={"method": request.method, "path": request.url.path,
                   "duration_ms": round((time.perf_counter() - started) * 1000, 2)},
        )
        raise
    finally:
        request_id_var.reset(token)

    response.headers["X-Request-ID"] = request_id
    if request.url.path not in {"/health", "/ready"}:
        logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(conversations_router)
app.include_router(collections_router)


@app.get("/")
async def root():
    return {
        "message": settings.app_name,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }


@app.get("/ready")
def readiness():
    checks = {"database": False, "redis": False, "storage": False}

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = True
    except SQLAlchemyError as exc:
        logger.warning("database_readiness_failed error=%s", exc)

    try:
        redis_client = Redis.from_url(settings.redis_url)
        checks["redis"] = bool(redis_client.ping())
        redis_client.close()
    except RedisError as exc:
        logger.warning("redis_readiness_failed error=%s", exc)

    checks["storage"] = check_storage_ready()

    ready = all(checks.values())
    payload = {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
    }

    return JSONResponse(
        status_code=200 if ready else 503,
        content=payload,
    )
