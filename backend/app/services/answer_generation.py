import logging
from dataclasses import dataclass

from openai import OpenAI

from app.config import settings
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


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


def _openai_client() -> OpenAI:
    client_kwargs: dict = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**client_kwargs)


def draft_answer_from_sources(question_text: str, retrieved_chunks: list[RetrievedChunk]) -> DraftAnswerResult:
    if not settings.openai_api_key:
        # No API key — deterministic fallback only
        if not retrieved_chunks:
            return DraftAnswerResult(
                draft_text="Insufficient source material found. Set OPENAI_API_KEY in .env to enable AI-generated answers.",
                citations=[],
                warning="No relevant knowledge base chunks found.",
            )
        citations = [
            CitationCandidate(
                chunk_id=item.chunk.id,
                document_title=item.chunk.document_title,
                section_title=item.chunk.section_title,
                page_number=item.chunk.page_number,
                excerpt=item.chunk.text.strip().replace("\n", " ")[:500],
                relevance_score=round(item.relevance_score, 4),
            )
            for item in retrieved_chunks[:3]
        ]
        return DraftAnswerResult(
            draft_text="\n\n".join(c.excerpt for c in citations)
                       + "\n\nReviewer note: Set OPENAI_API_KEY in .env to enable AI-generated answers.",
            citations=citations,
        )

    client = _openai_client()

    if not retrieved_chunks:
        # No knowledge context — ask OpenAI to answer from general knowledge
        logger.info("[OpenAI] Prompting with NO knowledge context for: %s", question_text[:80])
        print(f"\n[OpenAI] No knowledge context — prompting model '{settings.openai_model}' for: {question_text[:80]!r}\n")

        completion = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert RFP response writer. "
                        "No internal knowledge base excerpts are available for this question. "
                        "Write a professional, general-purpose response that a competent vendor would give. "
                        "Write in first-person plural (we/our). Keep the response under 200 words. "
                        "End with a note that this answer was generated without specific company knowledge and should be reviewed."
                    ),
                },
                {
                    "role": "user",
                    "content": f"RFP Requirement:\n{question_text}\n\nWrite a professional response.",
                },
            ],
            max_tokens=400,
            temperature=0.4,
        )
        draft_text = completion.choices[0].message.content or ""
        return DraftAnswerResult(
            draft_text=draft_text,
            citations=[],
            warning="No relevant knowledge base chunks found. Answer generated from general knowledge.",
        )

    # Knowledge context available
    selected = retrieved_chunks[:3]
    citations: list[CitationCandidate] = []
    context_blocks: list[str] = []

    for item in selected:
        chunk = item.chunk
        excerpt = chunk.text.strip().replace("\n", " ")[:500]
        context_blocks.append(f"[Source: {chunk.document_title}]\n{excerpt}")
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

    context = "\n\n".join(context_blocks)
    logger.info("[OpenAI] Prompting with %d knowledge chunks for: %s", len(citations), question_text[:80])
    print(f"\n[OpenAI] Prompting model '{settings.openai_model}' with {len(citations)} source chunk(s) for: {question_text[:80]!r}\n")

    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert RFP response writer. Using only the provided knowledge base excerpts, "
                    "write a concise, professional, and direct answer to the RFP requirement. "
                    "Do not invent facts not present in the sources. "
                    "Write in first-person plural (we/our). Keep the response under 200 words."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"RFP Requirement:\n{question_text}\n\n"
                    f"Knowledge base excerpts:\n{context}\n\n"
                    "Write a professional response to this requirement."
                ),
            },
        ],
        max_tokens=400,
        temperature=0.3,
    )

    draft_text = completion.choices[0].message.content or ""
    return DraftAnswerResult(draft_text=draft_text, citations=citations)
