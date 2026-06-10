"""
MinerU-based document parsing service.
Extracts text, tables, and images from PDFs with high fidelity.
"""
import os
import json
from pathlib import Path
from typing import Any

try:
    from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
    from magic_pdf.data.dataset import PymuDocDataset
    from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
    from magic_pdf.config.enums import SupportedPdfParseMethod
    HAS_MINERU = True
except ImportError:
    HAS_MINERU = False

from backend.core.config import settings
from backend.core.logger import logger


class MinerUService:
    """Parses PDFs via MinerU and returns extracted markdown + metadata."""

    def __init__(self):
        self.output_dir = Path(settings.mineru_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def parse_pdf(self, file_path: str) -> dict[str, Any]:
        """
        Parse a PDF file using MinerU, falling back to PyMuPDF if MinerU is not configured or fails.

        Returns:
            {
              "markdown": str,          # full markdown text
              "pages": int,             # number of pages
              "images": list[str],      # paths to extracted images
              "metadata": dict          # doc-level metadata
            }
        """
        file_path = Path(file_path)
        doc_name = file_path.stem
        doc_output_dir = self.output_dir / doc_name
        doc_output_dir.mkdir(parents=True, exist_ok=True)

        if not HAS_MINERU:
            logger.info("MinerU is not installed/available. Using PyMuPDF fallback.")
            return self._parse_pdf_fallback(file_path, doc_output_dir)

        try:
            logger.info(f"MinerU: starting parse for {file_path.name}")

            # MinerU readers/writers
            reader = FileBasedDataReader("")
            image_writer = FileBasedDataWriter(str(doc_output_dir / "images"))
            md_writer = FileBasedDataWriter(str(doc_output_dir))

            pdf_bytes = reader.read(str(file_path))
            dataset = PymuDocDataset(pdf_bytes)

            # Auto-detect whether to use OCR or text mode
            if dataset.classify() == SupportedPdfParseMethod.OCR:
                logger.info("MinerU: using OCR pipeline")
                infer_result = dataset.apply(doc_analyze, ocr=True)
                pipe_result = infer_result.pipe_ocr_mode(image_writer)
            else:
                logger.info("MinerU: using text/NLP pipeline")
                infer_result = dataset.apply(doc_analyze, ocr=False)
                pipe_result = infer_result.pipe_txt_mode(image_writer)

            # Dump markdown
            md_filename = f"{doc_name}.md"
            pipe_result.dump_md(md_writer, md_filename, "images")

            md_path = doc_output_dir / md_filename
            markdown_text = md_path.read_text(encoding="utf-8")
            logger.info(f"MinerU: first 500 chars of extracted text:\n{markdown_text[:500]}")

            # Collect extracted image paths
            images_dir = doc_output_dir / "images"
            image_paths = (
                [str(p) for p in images_dir.iterdir() if p.is_file()]
                if images_dir.exists()
                else []
            )

            # Content list for metadata
            content_list = pipe_result.get_content_list("images")
            page_count = self._extract_page_count(content_list)

            logger.info(
                f"MinerU: finished — {page_count} pages, "
                f"{len(markdown_text)} chars, {len(image_paths)} images"
            )

            return {
                "markdown": markdown_text,
                "pages": page_count,
                "images": image_paths,
                "metadata": {
                    "source_file": str(file_path),
                    "doc_name": doc_name,
                    "output_dir": str(doc_output_dir),
                    "parser": "mineru"
                },
            }

        except Exception as exc:
            logger.warning(f"MinerU parse failed for {file_path.name}: {exc}. Falling back to PyMuPDF.")
            try:
                return self._parse_pdf_fallback(file_path, doc_output_dir)
            except Exception as fallback_exc:
                logger.error(f"Fallback PyMuPDF parser also failed: {fallback_exc}")
                raise RuntimeError(f"Parsing failed: MinerU error: {exc} | PyMuPDF error: {fallback_exc}") from fallback_exc

    def _parse_pdf_fallback(self, file_path: Path, doc_output_dir: Path) -> dict[str, Any]:
        """Fallback PDF parser using PyMuPDF with better text extraction."""
        logger.info(f"Using PyMuPDF parsing for {file_path.name}")
        try:
            import fitz
            doc = fitz.open(file_path)
            markdown_parts = []

            for page_num, page in enumerate(doc, 1):
                # Use "blocks" mode — preserves reading order better than raw get_text()
                blocks = page.get_text("blocks", sort=True)  # sort=True fixes reading order
                page_lines = []

                for block in blocks:
                    # block = (x0, y0, x1, y1, text, block_no, block_type)
                    if block[6] == 0:  # type 0 = text block (skip images=1)
                        text = block[4].strip()
                        if text:
                            page_lines.append(text)

                if page_lines:
                    page_text = "\n\n".join(page_lines)
                    markdown_parts.append(f"## Page {page_num}\n\n{page_text}")
                else:
                    logger.warning(f"Page {page_num} has no extractable text — may be scanned/image-based")

            markdown_text = "\n\n".join(markdown_parts)

            # Warn if extraction looks empty or too short
            total_chars = len(markdown_text.replace(" ", "").replace("\n", ""))
            avg_chars_per_page = total_chars / max(len(doc), 1)
            if avg_chars_per_page < 50:
                logger.warning(
                    f"Very low text density ({avg_chars_per_page:.0f} chars/page). "
                    "PDF may be scanned. MinerU OCR mode is needed for accurate results."
                )

            page_count = len(doc)
            md_path = doc_output_dir / f"{file_path.stem}.md"
            md_path.write_text(markdown_text, encoding="utf-8")

            return {
                "markdown": markdown_text,
                "pages": page_count,
                "images": [],
                "metadata": {
                    "source_file": str(file_path),
                    "doc_name": file_path.stem,
                    "output_dir": str(doc_output_dir),
                    "parser": "pymupdf_fallback"
                }
            }
        except Exception as exc:
            raise RuntimeError(f"PyMuPDF extraction failed: {exc}") from exc

    # ------------------------------------------------------------------
    def _extract_page_count(self, content_list: list) -> int:
        pages = set()
        for item in content_list:
            if isinstance(item, dict) and "page_no" in item:
                pages.add(item["page_no"])
        return len(pages) or 1
