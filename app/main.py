from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from app.config import get_settings
from app.db import init_db
from app.errors import register_exception_handlers
from app.routers import attendance, auth, batches, institutions, monitoring, programme, sessions


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("TESTING") != "true":
        init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_exception_handlers(app)
app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(monitoring.router)
app.include_router(attendance.router)
app.include_router(institutions.router)
app.include_router(programme.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Attendance API is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
