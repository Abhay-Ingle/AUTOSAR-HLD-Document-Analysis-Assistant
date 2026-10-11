"""Combined entry point that mounts the backend API and the browser UI
under a single Uvicorn process so the application can run on a single
free-tier Render web service.

- API routes:  /health/*, /documents/*, /qa/*, /analysis/*
- UI routes:   / (home), /api/* (proxied to the API)
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

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

# Mount all backend API routes directly
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(qa_router)
app.include_router(analysis_router)


# ─── UI proxy endpoints ────────────────────────────────────────────────
# These re-use the same in-process routers so no HTTP hop is needed.

from app.api.documents import list_documents  # noqa: E402
from app.api.qa import ask as api_ask, QuestionRequest  # noqa: E402
from app.api.analysis import (  # noqa: E402
    list_entities,
    compare_documents as api_compare,
    validate_document as api_validate,
    list_findings as api_list_findings,
    CompareRequest,
)
from app.storage.db import get_db  # noqa: E402


@app.get("/api/status")
def ui_status():
    return {"status": "ready", "environment": "render"}


@app.get("/api/documents")
def ui_documents():
    db = next(get_db())
    try:
        return list_documents(db=db)
    finally:
        db.close()


@app.post("/api/upload")
async def ui_upload(
    file: UploadFile = File(...),
    title: str = Form("AUTOSAR HLD"),
    version_label: str = Form("v1.0"),
):
    from app.api.documents import upload_document
    db = next(get_db())
    try:
        result = await upload_document(
            file=file, title=title, version_label=version_label, db=db
        )
        return result
    finally:
        db.close()


@app.post("/api/ask")
async def ui_ask(payload: dict):
    db = next(get_db())
    try:
        req = QuestionRequest(**payload)
        return api_ask(request=req, db=db)
    finally:
        db.close()


@app.get("/api/entities/{document_id}")
def ui_entities(document_id: str):
    db = next(get_db())
    try:
        return list_entities(document_id=document_id, db=db)
    finally:
        db.close()


@app.post("/api/compare")
async def ui_compare(payload: dict):
    db = next(get_db())
    try:
        req = CompareRequest(**payload)
        return api_compare(request=req, db=db)
    finally:
        db.close()


@app.post("/api/validate/{document_id}")
def ui_validate(document_id: str):
    db = next(get_db())
    try:
        return api_validate(document_id=document_id, db=db)
    finally:
        db.close()


@app.get("/api/findings")
def ui_findings(document_id: str | None = None):
    db = next(get_db())
    try:
        return api_list_findings(document_id=document_id, db=db)
    finally:
        db.close()


# ─── Serve the browser UI page ─────────────────────────────────────────

from ui.web import PAGE  # noqa: E402


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the single-page browser UI with API calls pointing to self."""
    # Replace the backend URL references to point to the same origin
    page = PAGE.replace(
        "http://127.0.0.1:8000",
        ""
    ).replace(
        "http://localhost:8000",
        ""
    )
    return page
