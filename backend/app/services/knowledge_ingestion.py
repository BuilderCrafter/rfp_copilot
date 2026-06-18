from dataclasses import dataclass

from app.config import settings
from app.schemas.common import new_id


@dataclass(frozen=True)
class KnowledgeChunkCandidate:
    id: str
    document_id: str
    document_title: str
    text: str
    page_number: int | None
    section_title: str | None
    chunk_index: int


def chunk_knowledge_document(
    document_id: str,
    document_title: str,
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[KnowledgeChunkCandidate]:
    """Split a knowledge document into citation-ready chunks.

    The MVP splitter is paragraph-aware and character-limited. It intentionally avoids
    complex layout logic so the team can demonstrate the RAG loop quickly.
    """
    max_size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if not current:
            current = paragraph
            continue

        if len(current) + len(paragraph) + 2 <= max_size:
            current = f"{current}\n\n{paragraph}"
        else:
            chunks.append(current)
            tail = current[-overlap:] if overlap > 0 else ""
            current = f"{tail}\n\n{paragraph}".strip()

    if current:
        chunks.append(current)

    return [
        KnowledgeChunkCandidate(
            id=new_id("chunk"),
            document_id=document_id,
            document_title=document_title,
            text=chunk,
            page_number=None,
            section_title=None,
            chunk_index=index,
        )
        for index, chunk in enumerate(chunks)
    ]
