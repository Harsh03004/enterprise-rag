from fastapi import FastAPI

from app.core.config import settings

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.documents import router as documents_router
from app.api.routes.chat import router as chat_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "message": settings.app_name
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }