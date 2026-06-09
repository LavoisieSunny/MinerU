"""
LLM service backed by Ollama.
Supports streaming and non-streaming completions with RAG context injection.
"""
import json
from typing import AsyncIterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.core.logger import logger

RAG_SYSTEM_PROMPT = """You are a helpful, precise assistant that answers questions
based ONLY on the provided context documents.

Rules:
- Answer strictly from the context. Do not hallucinate or use outside knowledge.
- If the context doesn't contain enough information, say so clearly.
- Cite the document name when referencing specific information.
- Keep answers concise and well-structured.
- If asked about something outside the documents, politely redirect.
"""


def build_rag_prompt(query: str, context_chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        doc_label = chunk.get("doc_name") or chunk.get("doc_id", f"doc-{i}")
        context_parts.append(f"[{i}] **{doc_label}**\n{chunk['text']}")

    context_str = "\n\n---\n\n".join(context_parts)
    return f"""Context documents:
{context_str}

---
Question: {query}

Answer:"""


class LLMService:
    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_llm_model
        self._client = httpx.AsyncClient(timeout=120.0)

    # ------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(self, prompt: str, system: str = RAG_SYSTEM_PROMPT) -> str:
        """Non-streaming completion."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        resp = await self._client.post(f"{self.base_url}/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    async def stream(
        self, prompt: str, system: str = RAG_SYSTEM_PROMPT
    ) -> AsyncIterator[str]:
        """Streaming completion — yields text deltas."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
        }
        async with self._client.stream(
            "POST", f"{self.base_url}/api/chat", json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    delta = data.get("message", {}).get("content", "")
                    if delta:
                        yield delta
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

    async def close(self):
        await self._client.aclose()
