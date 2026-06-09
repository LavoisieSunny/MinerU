"""
Embedding service backed by Ollama (nomic-embed-text or any embed model).
"""
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.core.logger import logger


class EmbeddingService:
    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_embed_model
        self._client = httpx.AsyncClient(timeout=60.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def embed(self, text: str) -> list[float]:
        """Embed a single string."""
        resp = await self._client.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text},
        )
        resp.raise_for_status()
        embedding = resp.json()["embedding"]
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings sequentially (Ollama has no batch endpoint)."""
        embeddings = []
        for i, text in enumerate(texts):
            vec = await self.embed(text)
            embeddings.append(vec)
            if (i + 1) % 10 == 0:
                logger.debug(f"Embedded {i+1}/{len(texts)} chunks")
        return embeddings

    async def close(self):
        await self._client.aclose()
