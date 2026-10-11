from collections.abc import Sequence

from app.providers.contracts import RetrievedChunk


class ChromaVectorStore:
    """Persistent Chroma adapter with metadata filtering."""

    def __init__(self, host: str, port: int, collection: str) -> None:
        import chromadb

        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(collection)

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadata: Sequence[dict[str, str | int | float]],
    ) -> None:
        self._collection.upsert(
            ids=list(ids),
            documents=list(texts),
            embeddings=[list(item) for item in embeddings],
            metadatas=[dict(item) for item in metadata],
        )

    def query(
        self,
        embedding: Sequence[float],
        top_k: int,
        where: dict[str, str | int] | None = None,
    ) -> list[RetrievedChunk]:
        result = self._collection.query(
            query_embeddings=[list(embedding)],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            RetrievedChunk(
                id=chunk_id,
                content=document,
                metadata=metadata or {},
                score=1.0 - float(distance),
            )
            for chunk_id, document, metadata, distance in zip(
                ids, documents, metadatas, distances, strict=True
            )
        ]

