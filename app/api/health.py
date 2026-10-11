from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.storage.db import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness(
    db: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {
        "status": "ready",
        "database": "ok",
        "llm": f"ollama:{settings.ollama_model}",
        "embeddings": f"{settings.embedding_provider}:{settings.embedding_model}",
        "vector_store": f"chroma:{settings.chroma_host}:{settings.chroma_port}",
    }
