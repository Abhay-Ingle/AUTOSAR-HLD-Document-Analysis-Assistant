from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis import compare_entities, validate_chunks
from app.storage.db import get_db
from app.storage.models import (
    ArchitectureEntity,
    Document,
    Finding,
    FindingStatus,
    ReviewStatus,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


class CompareRequest(BaseModel):
    document_a: str
    document_b: str


def _entity_dict(entity: ArchitectureEntity, document: Document) -> dict[str, object]:
    return {
        "id": entity.id,
        "entity_type": entity.entity_type,
        "name": entity.name,
        "confidence": entity.confidence,
        "review_status": entity.review_status,
        "citation": (
            f"[{document.title} {document.version_label}, "
            f"p.{entity.source_page}, §{entity.section_path}]"
        ),
        "source_page": entity.source_page,
        "section": entity.section_path,
        "snippet": entity.source_snippet,
    }


@router.get("/documents/{document_id}/entities")
def list_entities(document_id: str, db: Session = Depends(get_db)) -> list[dict[str, object]]:  # noqa: B008
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return [_entity_dict(item, document) for item in document.entities]


@router.patch("/entities/{entity_id}")
def review_entity(
    entity_id: str,
    review_status: str,
    name: str | None = None,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, object]:
    entity = db.get(ArchitectureEntity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    try:
        entity.review_status = ReviewStatus(review_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid review status") from exc
    if name is not None and name.strip():
        entity.name = name.strip()
        entity.review_status = ReviewStatus.EDITED
    db.commit()
    return {"id": entity.id, "review_status": entity.review_status, "name": entity.name}


@router.post("/compare")
def compare_documents(
    request: CompareRequest, db: Session = Depends(get_db)  # noqa: B008
) -> dict[str, object]:
    left = db.get(Document, request.document_a)
    right = db.get(Document, request.document_b)
    if left is None or right is None:
        raise HTTPException(status_code=404, detail="Both documents must exist")
    left_items = [_entity_dict(item, left) for item in left.entities]
    right_items = [_entity_dict(item, right) for item in right.entities]
    changes = compare_entities(left_items, right_items)
    left_sections = {chunk.section_path: chunk for chunk in left.chunks if chunk.section_path}
    right_sections = {chunk.section_path: chunk for chunk in right.chunks if chunk.section_path}
    changed_sections: list[dict[str, object]] = []
    for section in sorted(left_sections.keys() & right_sections.keys()):
        before = left_sections[section]
        after = right_sections[section]
        if sha256(before.content.encode("utf-8")).digest() == sha256(
            after.content.encode("utf-8")
        ).digest():
            continue
        changed_sections.append(
            {
                "section": section,
                "before": {
                    "page": before.page_number,
                    "snippet": before.content[:500],
                    "citation": (
                        f"[{left.title} {left.version_label}, "
                        f"p.{before.page_number}, §{section}]"
                    ),
                },
                "after": {
                    "page": after.page_number,
                    "snippet": after.content[:500],
                    "citation": (
                        f"[{right.title} {right.version_label}, "
                        f"p.{after.page_number}, §{section}]"
                    ),
                },
            }
        )
    return {
        "from": {"id": left.id, "title": left.title, "version": left.version_label},
        "to": {"id": right.id, "title": right.title, "version": right.version_label},
        "changes": [change.__dict__ for change in changes],
        "changed_sections": changed_sections,
        "affected_entity_names": sorted({change.name for change in changes}),
    }


@router.post("/validate/{document_id}")
def validate_document(
    document_id: str, db: Session = Depends(get_db)  # noqa: B008
) -> dict[str, object]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = [
        {"content": chunk.content, "page": chunk.page_number, "section": chunk.section_path}
        for chunk in document.chunks
    ]
    findings = validate_chunks(chunks)
    saved: list[Finding] = []
    for finding in findings:
        row = Finding(
            document_id=document.id,
            rule=finding.rule,
            severity=finding.severity,
            message=finding.message,
            evidence=finding.evidence,
            status=FindingStatus.OPEN,
        )
        db.add(row)
        saved.append(row)
    db.commit()
    return {
        "document_id": document.id,
        "findings": [
            {
                "id": item.id,
                "rule": item.rule,
                "severity": item.severity,
                "message": item.message,
                "evidence": item.evidence,
                "status": item.status,
            }
            for item in saved
        ],
    }


@router.get("/findings")
def list_findings(
    document_id: str | None = None,
    db: Session = Depends(get_db),  # noqa: B008
) -> list[dict[str, object]]:
    statement = select(Finding).order_by(Finding.created_at.desc())
    if document_id:
        statement = statement.where(Finding.document_id == document_id)
    return [
        {
            "id": item.id,
            "document_id": item.document_id,
            "rule": item.rule,
            "severity": item.severity,
            "message": item.message,
            "evidence": item.evidence,
            "status": item.status,
        }
        for item in db.scalars(statement).all()
    ]
