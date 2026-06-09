#!/usr/bin/env bash
set -e
echo "=== RAG Chatbot Setup ==="
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
[ ! -f .env ] && cp .env.example .env && echo "Created .env — edit it before running."
echo ""
echo "=== Done ==="
echo "1. Edit backend/.env"
echo "2. docker run -p 3115:6333 qdrant/qdrant"
echo "3. ollama pull llama3.2 && ollama pull nomic-embed-text"
echo "4. uvicorn backend.main:app --reload"
echo "5. cd frontend && npm install && npm run dev"
