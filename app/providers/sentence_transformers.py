from collections.abc import Sequence
from typing import Any


class SentenceTransformerEmbeddings:
    """Lazy local embedding adapter; model weights are loaded only on first use."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: Any | None = None

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        vectors = self._model.encode(list(texts), normalize_embeddings=True)
        return vectors.tolist()

