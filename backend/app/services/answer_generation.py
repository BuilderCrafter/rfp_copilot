from dataclasses import dataclass

from app.services.retrieval import RetrievedChunk


@dataclass(frozen=True)
class CitationCandidate:
    chunk_id: str
    document_title: str
    section_title: str | None
    page_number: int | None
    excerpt: str
    relevance_score: float | None


@dataclass(frozen=True)
class DraftAnswerResult:
    draft_text: str
    citations: list[CitationCandidate]
    warning: str | None = None


def draft_answer_from_sources(question_text: str, retrieved_chunks: list[RetrievedChunk]) -> DraftAnswerResult:
    """Draft an answer from retrieved chunks.

    This is a safe deterministic fallback. The RAG owner can replace the text generation
    with an LLM call while preserving the same output shape and safety behavior.
    """
    if not retrieved_chunks:
        return DraftAnswerResult(
            draft_text=(
                "Insufficient source material was found to answer this question confidently. "
                "A human reviewer should add or confirm the required content."
            ),
            citations=[],
            warning="No relevant knowledge base chunks found.",
        )

    selected = retrieved_chunks[:3]
    source_summaries = []
    citations: list[CitationCandidate] = []

    for item in selected:
        chunk = item.chunk
        excerpt = chunk.text.strip().replace("\n", " ")[:350]
        source_summaries.append(excerpt)
        citations.append(
            CitationCandidate(
                chunk_id=chunk.id,
                document_title=chunk.document_title,
                section_title=chunk.section_title,
                page_number=chunk.page_number,
                excerpt=excerpt,
                relevance_score=round(item.relevance_score, 4),
            )
        )

    draft_text = (
        f"Based on the available company knowledge, the response to '{question_text}' should emphasize: "
        + " ".join(source_summaries)
        + "\n\nReviewer note: This draft was generated from retrieved source excerpts and should be checked before approval."
    )

    return DraftAnswerResult(draft_text=draft_text, citations=citations)
