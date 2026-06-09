"""
FastAPI routes for the RAG chatbot.
"""
from pathlib import Path

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from qdrant_client import AsyncQdrantClient

from backend.core.config import settings
from backend.core.logger import logger
from backend.models.schemas import (
    ChatRequest, ChatResponse, DocumentInfo,
    DocumentListResponse, HealthResponse, IngestResponse,
)
from backend.services.rag_pipeline import RAGPipeline

router = APIRouter()
pipeline = RAGPipeline()


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    ollama_status, qdrant_status = "unreachable", "unreachable"
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{settings.ollama_base_url}/api/tags")
            ollama_status = "ok" if r.status_code == 200 else "error"
    except Exception:
        pass
    try:
        client = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        await client.get_collections()
        qdrant_status = "ok"
    except Exception:
        pass
    return HealthResponse(
        status="ok" if ollama_status == qdrant_status == "ok" else "degraded",
        ollama=ollama_status, qdrant=qdrant_status, model=settings.ollama_llm_model,
    )


@router.post("/documents/upload", response_model=IngestResponse, tags=["documents"])
async def upload_document(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(400, f"File type '{ext}' not allowed.")
    upload_path = Path(settings.upload_dir) / file.filename
    size = 0
    with open(upload_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_size_mb * 1024 * 1024:
                upload_path.unlink(missing_ok=True)
                raise HTTPException(413, f"File exceeds {settings.max_upload_size_mb} MB limit")
            f.write(chunk)
    try:
        result = await pipeline.ingest_document(str(upload_path))
    except Exception as exc:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(500, str(exc))
    return IngestResponse(**result)


@router.get("/documents", response_model=DocumentListResponse, tags=["documents"])
async def list_documents():
    docs = await pipeline.list_documents()
    return DocumentListResponse(documents=[DocumentInfo(**d) for d in docs], total=len(docs))


@router.delete("/documents/{doc_id}", tags=["documents"])
async def delete_document(doc_id: str):
    await pipeline.delete_document(doc_id)
    return {"message": f"Document '{doc_id}' deleted"}


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest):
    try:
        result = await pipeline.query(question=request.question, doc_id=request.doc_id, stream=False)
        return ChatResponse(**result)
    except Exception as exc:
        raise HTTPException(500, str(exc))


@router.post("/chat/stream", tags=["chat"])
async def chat_stream(request: ChatRequest):
    try:
        stream_gen = await pipeline.query(question=request.question, doc_id=request.doc_id, stream=True)
        async def event_generator():
            async for token in stream_gen:
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as exc:
        raise HTTPException(500, str(exc))
