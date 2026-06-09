from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    doc_id: str
    doc_name: str
    chunks_indexed: int
    pages: int
    images_extracted: int
    message: str = "Document ingested successfully"


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    doc_id: str | None = Field(None, description="Scope search to a specific document")
    stream: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    chunks_used: int = 0
    top_chunk_score: float = 0.0


class DocumentInfo(BaseModel):
    doc_id: str
    doc_name: str
    source_file: str
    pages: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int


class HealthResponse(BaseModel):
    status: str
    ollama: str
    qdrant: str
    model: str
