from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class VectorStoreService:
    """Manages per-user ChromaDB collections with local sentence-transformer embeddings."""

    def __init__(self):
        self._client: chromadb.PersistentClient | None = None
        self._model: SentenceTransformer | None = None

    def _client_(self) -> chromadb.PersistentClient:
        if self._client is None:
            Path(settings.vector_db_path).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=settings.vector_db_path)
        return self._client

    def _embedding_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def _collection(self, user_id: int):
        return self._client_().get_or_create_collection(
            name=f"user_{user_id}",
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, user_id: int, document_id: int, chunks: list[str], filename: str) -> None:
        if not chunks:
            return
        embeddings = self._embedding_model().encode(chunks, show_progress_bar=False).tolist()
        ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"document_id": document_id, "filename": filename, "chunk_index": i}
            for i in range(len(chunks))
        ]
        self._collection(user_id).add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

    def search(self, user_id: int, query: str, top_k: int = 5) -> list[dict]:
        collection = self._collection(user_id)
        count = collection.count()
        if count == 0:
            return []
        query_embedding = self._embedding_model().encode([query], show_progress_bar=False).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, count),
        )
        return [
            {"content": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def delete_document(self, user_id: int, document_id: int) -> None:
        collection = self._collection(user_id)
        results = collection.get(where={"document_id": document_id})
        if results["ids"]:
            collection.delete(ids=results["ids"])


vector_store_service = VectorStoreService()