import re

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.storage.db import get_db
from app.storage.models import Document, DocumentChunk, DocumentStatus

router = APIRouter(prefix="/qa", tags=["search and Q&A"])


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    document_id: str | None = None
    project: str | None = None
    version: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


def _tokens(value: str) -> set[str]:
    stop_words = {
        "what", "which", "where", "when", "does", "have", "from", "with", "this",
        "that", "are", "the", "and", "for", "about", "please", "show", "tell",
    }
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_]+", value)
        if len(token) > 2 and token.lower() not in stop_words
    }


def _snippet(content: str, query_tokens: set[str], limit: int = 420) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", content.strip())
    relevant = [sentence for sentence in sentences if query_tokens & _tokens(sentence)]
    value = " ".join(relevant[:2]) or content.strip()
    return value[:limit].strip()


def _local_answer(question: str, selected: list[tuple[int, DocumentChunk, Document]]) -> str | None:
    settings = get_settings()
    context = "\n\n".join(
        f"[S{index + 1}] {document.title} {document.version_label}, "
        f"p.{chunk.page_number}, §{chunk.section_path}\n"
        f"{_snippet(chunk.content, _tokens(question))}"
        for index, (_, chunk, document) in enumerate(selected)
    )
    prompt = (
        "Answer the exact question first using only the evidence below. "
        "Do not infer missing architecture relationships. Keep the answer concise. "
        "Cite every factual claim using the supplied [S#] marker. "
        "If the evidence does not answer the question, reply exactly: "
        "'Not found in the provided documents.'\n\n"
        f"Question: {question}\nEvidence:\n{context}"
    )
    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=8,
        )
        response.raise_for_status()
        answer = response.json().get("response")
        if isinstance(answer, str) and answer.strip() and re.search(r"\[S\d+\]", answer):
            return answer.strip()
    except (httpx.HTTPError, ValueError, KeyError):
        return None
    return None


@router.post("/ask")
def ask(request: QuestionRequest, db: Session = Depends(get_db)) -> dict[str, object]:  # noqa: B008
    query_tokens = _tokens(request.question)
    rows = db.execute(
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.status == DocumentStatus.APPROVED)
    ).all()
    scored = []
    for chunk, document in rows:
        if request.document_id and document.id != request.document_id:
            continue
        if request.project and document.project.name != request.project:
            continue
        if request.version and document.version_label != request.version:
            continue
        score = len(query_tokens & _tokens(chunk.content))
        score += 2 * len(query_tokens & _tokens(chunk.section_path))
        if score:
            scored.append((score, chunk, document))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = scored[: request.top_k]
    if not selected:
        return {
            "answer": "Not found in the provided documents.",
            "citations": [],
            "sources": [],
            "confidence": 0.0,
        }
    citations = [
        f"[{document.title} {document.version_label}, p.{chunk.page_number}, §{chunk.section_path}]"
        for _, chunk, document in selected
    ]
    answer = _local_answer(request.question, selected)
    if answer:
        for index, citation in enumerate(citations, start=1):
            answer = answer.replace(f"[S{index}]", citation)
    else:
        answer = "Evidence summary: " + " ".join(
            f"{_snippet(chunk.content, query_tokens)} {citations[index]}"
            for index, (_, chunk, _) in enumerate(selected[:3])
        )
    return {
        "answer": answer,
        "citations": citations,
        "sources": [
            {
                "document": document.title,
                "version": document.version_label,
                "page": chunk.page_number,
                "section": chunk.section_path,
                "snippet": _snippet(chunk.content, query_tokens),
                "score": score,
            }
            for score, chunk, document in selected
        ],
        "confidence": min(0.95, 0.5 + 0.1 * len(selected)),
    }
