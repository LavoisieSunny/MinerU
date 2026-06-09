"""
High-level RAG pipeline.
Ties together: ingest (MinerU → chunk → embed → store) and query (embed → search → LLM).
"""
import uuid
from pathlib import Path
from typing import Any, AsyncIterator

from backend.services.mineru_service import MinerUService
from backend.services.chunker_service import ChunkerService
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store_service import VectorStoreService
from backend.services.llm_service import LLMService, build_rag_prompt
from backend.core.config import settings
from backend.core.logger import logger


class RAGPipeline:
    def __init__(self):
        self.mineru = MinerUService()
        self.chunker = ChunkerService()
        self.embedder = EmbeddingService()
        self.vector_store = VectorStoreService()
        self.llm = LLMService()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    async def ingest_document(self, file_path: str) -> dict[str, Any]:
        """
        Full ingestion pipeline:
          1. Parse with MinerU
          2. Chunk markdown
          3. Embed chunks
          4. Upsert into Qdrant
        """
        doc_id = str(uuid.uuid4())
        file_path = Path(file_path)
        logger.info(f"RAG ingest: start — {file_path.name} [{doc_id}]")

        # 1. Parse
        parse_result = await self.mineru.parse_pdf(str(file_path))
        markdown = parse_result["markdown"]

        if not markdown.strip():
            raise ValueError("MinerU returned empty content — check the PDF.")

        # 2. Chunk
        chunk_metadata = {
            "doc_id": doc_id,
            "doc_name": file_path.stem,
            "source_file": str(file_path),
            "pages": parse_result["pages"],
        }
        chunks = self.chunker.chunk_text(markdown, metadata=chunk_metadata)
        logger.info(f"RAG ingest: {len(chunks)} chunks created")

        # 3. Embed
        texts = [c["text"] for c in chunks]
        embeddings = await self.embedder.embed_batch(texts)

        # 4. Store
        count = await self.vector_store.upsert_chunks(chunks, embeddings, doc_id)

        result = {
            "doc_id": doc_id,
            "doc_name": file_path.stem,
            "chunks_indexed": count,
            "pages": parse_result["pages"],
            "images_extracted": len(parse_result["images"]),
        }
        logger.info(f"RAG ingest: done — {result}")
        return result

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------
    async def query(
        self,
        question: str,
        doc_id: str | None = None,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[str]:
        """
        RAG query pipeline:
          1. Embed question
          2. Retrieve top-k chunks from Qdrant
          3. Build prompt and call LLM
        """
        logger.info(f"RAG query: '{question[:80]}...' | doc_id={doc_id}")

        # 1. Embed
        query_vector = await self.embedder.embed(question)

        # 2. Retrieve
        chunks = await self.vector_store.search(
            query_vector=query_vector,
            top_k=settings.top_k_results,
            score_threshold=settings.similarity_threshold,
            doc_id=doc_id,
        )

        if not chunks:
            no_context_msg = (
                "I couldn't find relevant context in the indexed documents "
                "to answer your question."
            )
            if stream:
                async def _empty():
                    yield no_context_msg
                return _empty()
            return {"answer": no_context_msg, "sources": [], "chunks_used": 0}

        # 3. LLM
        prompt = build_rag_prompt(question, chunks)
        sources = list({c["doc_name"] for c in chunks if c.get("doc_name")})

        if stream:
            return self.llm.stream(prompt)

        answer = await self.llm.complete(prompt)
        return {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(chunks),
            "top_chunk_score": chunks[0]["score"] if chunks else 0,
        }

    async def delete_document(self, doc_id: str):
        await self.vector_store.delete_doc(doc_id)
        logger.info(f"RAG: deleted doc '{doc_id}'")

    async def list_documents(self) -> list[dict[str, Any]]:
        return await self.vector_store.list_documents()
