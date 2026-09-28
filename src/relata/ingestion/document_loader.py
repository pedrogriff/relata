"""Document loading and text extraction utilities for corporate filings and meeting minutes."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader


def load_document(source: str | Path | bytes | BinaryIO, filename_hint: str | None = None) -> str:
    """Loads and normalizes raw text from PDF files, plain text, or in-memory byte buffers.

    Args:
        source: File path, Path object, raw bytes, or file-like binary stream.
        filename_hint: Optional file name to disambiguate file type when source is bytes.

    Returns:
        Clean, normalized plain text representation of the document.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Document not found at path: {path}")

        if path.suffix.lower() == ".pdf":
            reader = PdfReader(str(path))
            return _extract_pdf_pages(reader)
        return _normalize_text(path.read_text(encoding="utf-8", errors="replace"))

    if isinstance(source, bytes):
        hint = (filename_hint or "").lower()
        if source.startswith(b"%PDF") or hint.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(source))
            return _extract_pdf_pages(reader)
        return _normalize_text(source.decode("utf-8", errors="replace"))

    # File-like object
    reader = PdfReader(source)
    return _extract_pdf_pages(reader)


def _extract_pdf_pages(reader: PdfReader) -> str:
    """Extracts text across all pages in a PDF document with page boundary annotations."""
    page_texts: list[str] = []
    for idx, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        clean = _normalize_text(raw)
        if clean:
            page_texts.append(f"--- [PÁGINA {idx + 1}] ---\n{clean}")
    return "\n\n".join(page_texts)


def _normalize_text(text: str) -> str:
    """Strips excessive control characters and collapses redundant whitespace."""
    # Collapse multiple blank lines to at most two
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip non-printable control characters except standard whitespace
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    return text.strip()
