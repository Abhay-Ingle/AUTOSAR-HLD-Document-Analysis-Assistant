from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned by a vector or hybrid retriever."""

    id: str
    content: str
    metadata: dict[str, str | int | float]
    score: float


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate text using a locally hosted model."""


class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Create embeddings without leaving the private deployment."""


class VectorStore(Protocol):
    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadata: Sequence[dict[str, str | int | float]],
    ) -> None:
        """Persist chunks and their embeddings."""

    def query(
        self,
        embedding: Sequence[float],
        top_k: int,
        where: dict[str, str | int] | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant chunks with optional metadata filters."""

