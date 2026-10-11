from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.qa import router as qa_router
from app.core.config import get_settings
from app.storage.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    Path(settings.app_data_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="AUTOSAR HLD Document Analysis Assistant",
    version="0.1.0",
    description="Private, evidence-first foundation for AUTOSAR architecture analysis.",
    lifespan=lifespan,
)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(qa_router)
app.include_router(analysis_router)
