from pathlib import Path

import fitz  # PyMuPDF
from docx import Document as DocxDocument


SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


class UnsupportedDocumentError(ValueError):
    """Raised when a document format is not supported by the MVP parser."""


def extract_text_from_file(path: Path) -> str:
    """Extract plain text from supported RFP/knowledge document formats.

    The MVP keeps parsing intentionally simple. More advanced layout, table extraction,
    page metadata, and OCR can be added later without changing API contracts.
    """
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise UnsupportedDocumentError(f"Unsupported file type: {suffix}")

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".docx":
        doc = DocxDocument(path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())

    if suffix == ".pdf":
        with fitz.open(path) as pdf:
            pages = [page.get_text("text") for page in pdf]
        return "\n".join(pages)

    raise UnsupportedDocumentError(f"Unsupported file type: {suffix}")
