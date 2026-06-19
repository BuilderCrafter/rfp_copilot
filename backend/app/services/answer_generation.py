import json
import logging
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

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


def _clamp_trust_score(value: object) -> float | None:
    if not isinstance(value, int | float):
        return None
    return max(0.0, min(1.0, float(value)))


def _parse_json_object(raw_content: str) -> dict:
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        start = raw_content.find("{")
        end = raw_content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(raw_content[start : end + 1])

    return parsed if isinstance(parsed, dict) else {}


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
        print(f"\n[OpenAI] No knowledge context — prompting model '{settings.openai_model}' for: {question_text[:80]!r}\n", flush=True)

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

    # Knowledge context available. Lexical retrieval only chooses candidate sources;
    # OpenAI estimates citation trust for the percentages shown in the UI.
    selected = retrieved_chunks[:3]
    context_blocks: list[str] = []

    for index, item in enumerate(selected, start=1):
        chunk = item.chunk
        excerpt = chunk.text.strip().replace("\n", " ")[:500]
        context_blocks.append(
            f"[source_index: {index}; source_document: {chunk.document_title}; "
            f"chunk_id: {chunk.id}]\n{excerpt}"
        )

    context = "\n\n".join(context_blocks)
    logger.info("[OpenAI] Prompting with %d knowledge chunks for: %s", len(selected), question_text[:80])
    print(f"\n[OpenAI] Prompting model '{settings.openai_model}' with {len(selected)} source chunk(s) for: {question_text[:80]!r}\n")

    try:
        completion = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert RFP response writer and source support reviewer. "
                        "Using only the provided knowledge base excerpts, write a concise, professional, "
                        "direct answer to the RFP requirement. Do not invent facts not present in the sources. "
                        "Write in first-person plural (we/our). Keep the answer under 200 words. "
                        "Then estimate source trust for each cited source as a number from 0.0 to 1.0. "
                        "Trust means how strongly that source supports the generated answer for this exact "
                        "requirement: 1.0 direct support, 0.7 strong partial support, 0.4 weak support, "
                        "0.1 topical only, 0.0 no support. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"RFP Requirement:\n{question_text}\n\n"
                        f"Knowledge base excerpts:\n{context}\n\n"
                        "Return this JSON shape exactly:\n"
                        "{\n"
                        '  "answer": "professional answer text",\n'
                        '  "citations": [\n'
                        '    {"source_index": 1, "trust_score": 0.0},\n'
                        '    {"source_index": 2, "trust_score": 0.0},\n'
                        '    {"source_index": 3, "trust_score": 0.0}\n'
                        "  ]\n"
                        "}"
                    ),
                },
            ],
            max_tokens=650,
            temperature=0.3,
        )
        parsed = _parse_json_object(completion.choices[0].message.content or "{}")
    except (OpenAIError, json.JSONDecodeError):
        logger.exception("OpenAI answer/trust generation failed.")
        return DraftAnswerResult(
            draft_text="Unable to generate an OpenAI-backed response right now. Please try again.",
            citations=[],
            warning="OpenAI answer and trust estimation failed.",
        )

    draft_text = parsed.get("answer") if isinstance(parsed.get("answer"), str) else ""
    trust_by_source_index: dict[int, float] = {}
    raw_citations = parsed.get("citations")
    if isinstance(raw_citations, list):
        for item in raw_citations:
            if not isinstance(item, dict):
                continue
            source_index = item.get("source_index")
            if not isinstance(source_index, int):
                continue
            trust_score = _clamp_trust_score(item.get("trust_score"))
            if trust_score is not None:
                trust_by_source_index[source_index] = trust_score

    citations = [
        CitationCandidate(
            chunk_id=item.chunk.id,
            document_title=item.chunk.document_title,
            section_title=item.chunk.section_title,
            page_number=item.chunk.page_number,
            excerpt=item.chunk.text.strip().replace("\n", " ")[:500],
            relevance_score=trust_by_source_index.get(index),
        )
        for index, item in enumerate(selected, start=1)
    ]

    return DraftAnswerResult(draft_text=draft_text, citations=citations)
