# RAG Chatbot — MinerU + Ollama + Qdrant + FastAPI

A production-ready RAG chatbot that parses PDFs with **MinerU**, embeds chunks via **Ollama**, stores vectors in **Qdrant**, and serves a streaming chat UI built with **FastAPI + React**.

## Stack

| Layer | Technology |
|---|---|
| PDF parsing | MinerU (magic-pdf) |
| LLM | Ollama (llama3.2 or any local model) |
| Embeddings | Ollama (nomic-embed-text) |
| Vector DB | Qdrant |
| Backend | FastAPI + Uvicorn |
| Frontend | React + Vite |

## Quick Start

```bash
# 1. Qdrant
docker run -p 3115:6333 qdrant/qdrant

# 2. Ollama models (on your server)
ollama pull llama3.2
ollama pull nomic-embed-text

# 3. Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
uvicorn backend.main:app --reload --port 3110

# 4. Frontend
cd frontend && npm install && npm run dev
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /api/v1/health | Health check |
| POST | /api/v1/documents/upload | Upload & ingest PDF |
| GET | /api/v1/documents | List documents |
| DELETE | /api/v1/documents/{doc_id} | Delete document |
| POST | /api/v1/chat | Non-streaming chat |
| POST | /api/v1/chat/stream | Streaming SSE chat |

Swagger UI: http://localhost:3110/api/docs
