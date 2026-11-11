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
from app.db.session import engine
from app.services.document_service import check_storage_ready

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("enterprise_rag.api")


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
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
