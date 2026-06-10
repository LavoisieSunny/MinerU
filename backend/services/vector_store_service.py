"""
Qdrant vector store service.
Handles collection management, upsert, and similarity search.
"""
import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    ScoredPoint,
)

from backend.core.config import settings
from backend.core.logger import logger


class VectorStoreService:
    def __init__(self):
        self.client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.collection = settings.qdrant_collection_name
        self.vector_size = settings.qdrant_vector_size

    # ------------------------------------------------------------------
    # Collection lifecycle
    # ------------------------------------------------------------------
    async def ensure_collection(self):
        response = await self.client.get_collections()
        existing = {c.name for c in response.collections}
        if self.collection not in existing:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=Distance.COSINE
                ),
            )
            logger.info(f"Qdrant: created collection '{self.collection}'")
        else:
            logger.debug(f"Qdrant: collection '{self.collection}' already exists")

    async def delete_collection(self):
        await self.client.delete_collection(self.collection)
        logger.warning(f"Qdrant: deleted collection '{self.collection}'")

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------
    async def upsert_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
        doc_id: str,
    ) -> int:
        """Upsert chunk embeddings with metadata payloads."""
        await self.ensure_collection()

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "doc_id": doc_id,
                    "text": chunk["text"],
                    "chunk_index": chunk.get("chunk_index", i),
                    "source_file": chunk.get("source_file", ""),
                    "doc_name": chunk.get("doc_name", ""),
                    "pages": chunk.get("pages", 0),
                },
            )
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]

        await self.client.upsert(collection_name=self.collection, points=points)
        logger.info(f"Qdrant: upserted {len(points)} points for doc '{doc_id}'")
        return len(points)

    async def delete_doc(self, doc_id: str):
        """Remove all vectors belonging to a document."""
        await self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
        )
        logger.info(f"Qdrant: deleted vectors for doc '{doc_id}'")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    async def search(
        self,
        query_vector: list[float],
        top_k: int = settings.top_k_results,
        score_threshold: float = settings.similarity_threshold,
        doc_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return top-k similar chunks with their payloads."""
        query_filter = None
        if doc_id:
            query_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )

        results: list[ScoredPoint] = await self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        if results:
            best_score = results[0].score
            logger.info(f"Qdrant search: best_score={best_score:.3f}, threshold={score_threshold}")
            if best_score < score_threshold:
                logger.warning(
                    f"Best score {best_score:.3f} is below threshold {score_threshold} — "
                    "returning results anyway. Consider lowering similarity_threshold in config."
                )

        return [
            {
                "score": r.score,
                "text": r.payload.get("text", ""),
                "doc_id": r.payload.get("doc_id"),
                "doc_name": r.payload.get("doc_name"),
                "chunk_index": r.payload.get("chunk_index"),
                "source_file": r.payload.get("source_file"),
            }
            for r in results
        ]

    async def list_documents(self) -> list[dict[str, Any]]:
        """Return distinct documents indexed in the collection."""
        await self.ensure_collection()
        # Scroll through all points and aggregate doc metadata
        seen_docs: dict[str, dict] = {}
        offset = None

        while True:
            records, offset = await self.client.scroll(
                collection_name=self.collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for rec in records:
                doc_id = rec.payload.get("doc_id")
                if doc_id and doc_id not in seen_docs:
                    seen_docs[doc_id] = {
                        "doc_id": doc_id,
                        "doc_name": rec.payload.get("doc_name", ""),
                        "source_file": rec.payload.get("source_file", ""),
                        "pages": rec.payload.get("pages", 0),
                    }
            if offset is None:
                break

        return list(seen_docs.values())
