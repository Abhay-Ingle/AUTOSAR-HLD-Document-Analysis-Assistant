from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.extraction import extract_entities_from_chunks
from app.ingestion.pdf import file_sha256, parse_pdf
from app.storage.db import get_db
from app.storage.models import (
    ArchitectureEntity,
    Document,
    DocumentChunk,
    DocumentStatus,
    Project,
    ReviewStatus,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _store_chunks_and_entities(
    db: Session, document: Document, chunks: list[object]
) -> None:
    db.execute(delete(ArchitectureEntity).where(ArchitectureEntity.document_id == document.id))
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    for chunk in chunks:
        db.add(
            DocumentChunk(
                document_id=document.id,
                page_number=chunk.page_number,
                section_path=chunk.section_path,
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                vector_id=f"{document.id}:{chunk.page_number}:{uuid4()}",
            )
        )
    for entity in extract_entities_from_chunks(chunks):
        db.add(
            ArchitectureEntity(
                document_id=document.id,
                entity_type=entity.entity_type,
                name=entity.name,
                source_page=entity.source_page,
                section_path=entity.section_path,
                source_snippet=entity.source_snippet,
                confidence=entity.confidence,
                review_status=ReviewStatus.PENDING,
            )
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),  # noqa: B008
    project: str = Form("Default Project"),  # noqa: B008
    title: str = Form("AUTOSAR HLD"),  # noqa: B008
    version_label: str = Form("v1.0"),  # noqa: B008
    revision: str = Form("Initial"),  # noqa: B008
    status: DocumentStatus = Form(DocumentStatus.APPROVED),  # noqa: B008
    uploaded_by: str = Form("Engineer"),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, object]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty")
    digest = file_sha256(data)
    project_row = db.scalar(select(Project).where(Project.name == project))
    if project_row is None:
        project_row = Project(name=project)
        db.add(project_row)
        db.flush()
    existing = db.scalar(
        select(Document).where(
            Document.project_id == project_row.id, Document.file_hash == digest
        )
    )
    if existing:
        return {
            "document_id": existing.id,
            "status": "already_ingested",
            "chunks": len(existing.chunks),
        }
    settings = get_settings()
    folder = Path(settings.app_data_dir) / "documents"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid4()}.pdf"
    path.write_bytes(data)
    chunks = parse_pdf(path)
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No selectable text found; OCR is required for this PDF",
        )
    document = Document(
        project_id=project_row.id,
        title=title,
        version_label=version_label,
        revision=revision,
        status=status,
        file_hash=digest,
        file_path=str(path),
        uploaded_by=uploaded_by,
    )
    db.add(document)
    db.flush()
    _store_chunks_and_entities(db, document, chunks)
    db.commit()
    return {
        "document_id": document.id,
        "status": "ingested",
        "pages": len({chunk.page_number for chunk in chunks}),
        "chunks": len(chunks),
        "entities": len(document.entities),
    }


@router.post("/{document_id}/reindex")
def reindex_document(document_id: str, db: Session = Depends(get_db)) -> dict[str, object]:  # noqa: B008
    """Rebuild derived chunks/entities while leaving the source PDF untouched."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    path = Path(document.file_path)
    if not path.exists():
        raise HTTPException(status_code=422, detail="Original source PDF is unavailable")
    chunks = parse_pdf(path)
    if not chunks:
        raise HTTPException(status_code=422, detail="No text or OCR content found")
    _store_chunks_and_entities(db, document, chunks)
    db.commit()
    return {
        "document_id": document.id,
        "status": "reindexed",
        "pages": len({chunk.page_number for chunk in chunks}),
        "chunks": len(chunks),
        "entities": len(extract_entities_from_chunks(chunks)),
    }


@router.get("")
def list_documents(db: Session = Depends(get_db)) -> list[dict[str, object]]:  # noqa: B008
    documents = db.scalars(select(Document).order_by(Document.uploaded_at.desc())).all()
    return [
        {
            "id": item.id,
            "title": item.title,
            "version": item.version_label,
            "project": item.project.name,
            "status": item.status,
            "chunks": len(item.chunks),
            "entities": len(item.entities),
        }
        for item in documents
    ]
