"""
Text chunking service with overlap.
Splits MinerU markdown output into semantically coherent chunks.
"""
import re
from typing import Any

from backend.core.config import settings
from backend.core.logger import logger


class ChunkerService:
    def __init__(
        self,
        chunk_size: int = settings.chunk_size,
        chunk_overlap: int = settings.chunk_overlap,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Split text into overlapping chunks.
        Respects paragraph / heading boundaries where possible.
        """
        metadata = metadata or {}
        paragraphs = self._split_paragraphs(text)
        chunks: list[dict[str, Any]] = []
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk_size, flush
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(self._make_chunk(current_chunk, chunk_idx, metadata))
                chunk_idx += 1
                # Keep tail for overlap
                current_chunk = current_chunk[-self.chunk_overlap :] + "\n\n" + para
            else:
                current_chunk = (current_chunk + "\n\n" + para).strip()

        if current_chunk.strip():
            chunks.append(self._make_chunk(current_chunk, chunk_idx, metadata))

        logger.debug(f"Chunker: {len(text)} chars → {len(chunks)} chunks")
        return chunks

    # ------------------------------------------------------------------
    @staticmethod
    def _split_paragraphs(text: str) -> list[str]:
        """Split on blank lines; keep markdown headings as their own paragraph."""
        parts = re.split(r"\n{2,}", text)
        result: list[str] = []
        for p in parts:
            # Headings always start a new chunk
            if p.startswith("#"):
                result.append(p)
            elif len(p) > 1000:
                # Long paragraphs: split on sentence boundaries
                sentences = re.split(r"(?<=[.!?])\s+", p)
                buf = ""
                for s in sentences:
                    if len(buf) + len(s) > 800:
                        if buf:
                            result.append(buf)
                        buf = s
                    else:
                        buf = (buf + " " + s).strip()
                if buf:
                    result.append(buf)
            else:
                result.append(p)
        return result

    @staticmethod
    def _make_chunk(
        text: str, idx: int, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "text": text.strip(),
            "chunk_index": idx,
            "char_count": len(text),
            **metadata,
        }
