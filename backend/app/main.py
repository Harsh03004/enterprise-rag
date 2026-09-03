from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.documents import router as documents_router
from app.api.routes.chat import router as chat_router

from app.api.routes.conversations import (
    router as conversations_router,
)
from app.api.routes.collections import (
    router as collections_router,
)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(chat_router)
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