import json

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DocumentRecord, KnowledgeChunkRecord, RfpAssessmentRecord
from app.schemas.assessment import (
    BidFactor,
    BidRecommendation,
    ClientSubmissionItem,
    MissingInfoItem,
    RfpAssessment,
    RfpChecklistItem,
)
from app.schemas.common import new_id, utc_now
from app.schemas.document import DocumentType, KnowledgeChunk


class RfpAssessmentUnavailable(Exception):
    """Raised when a project does not have enough source material to assess."""


class AssessmentDraft(BaseModel):
    recommendation: BidRecommendation
    bid_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    summary: str
    policy_source_documents: list[str] = Field(default_factory=list)
    bid_factors: list[BidFactor] = Field(default_factory=list)
    checklist: list[RfpChecklistItem] = Field(default_factory=list)
    missing_information: list[MissingInfoItem] = Field(default_factory=list)
    client_submission_checklist: list[ClientSubmissionItem] = Field(default_factory=list)


MAX_RFP_CONTEXT_CHARS = 24000
MAX_KNOWLEDGE_CONTEXT_CHARS = 90000
MAX_CHUNK_CONTEXT_CHARS = 1400


def _openai_client() -> OpenAI:
    client_kwargs: dict = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**client_kwargs)


def _compact(text: str, max_chars: int) -> str:
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].rstrip() + "\n[truncated]"


def _knowledge_context(knowledge_chunks: list[KnowledgeChunk]) -> str:
    parts: list[str] = []
    used_chars = 0

    for chunk in sorted(
        knowledge_chunks,
        key=lambda item: (item.document_title.lower(), item.chunk_index),
    ):
        excerpt = _compact(chunk.text, MAX_CHUNK_CONTEXT_CHARS)
        block = (
            f"[source_document: {chunk.document_title}; chunk_id: {chunk.id}; "
            f"chunk_index: {chunk.chunk_index}]\n{excerpt}"
        )
        next_size = len(block) + 2
        if used_chars + next_size > MAX_KNOWLEDGE_CONTEXT_CHARS:
            break
        parts.append(block)
        used_chars += next_size

    return "\n\n".join(parts)


def _assessment_prompt(rfp_text: str, knowledge_chunks: list[KnowledgeChunk]) -> str:
    return f"""
Analyze this RFP using the company's unified knowledge base. Return one JSON object only.

Use the knowledge base as the authority for:
- what the company requires from RFPs,
- bid/no-bid criteria,
- missing information to request from the buyer,
- materials the company must provide to the client in the proposal package.

Do not use fixed keyword rules. Infer requirements from the RFP text and the knowledge base.
Do not invent facts about company certifications or available documents. Mark uncertain items as
needs_review or conditional.

Required JSON shape:
{{
  "recommendation": "bid | no_bid | needs_review",
  "bid_score": 0,
  "confidence": 0.0,
  "summary": "short bid/no-bid rationale",
  "policy_source_documents": ["knowledge document titles used"],
  "bid_factors": [
    {{
      "id": "snake_case_id",
      "label": "factor name",
      "sentiment": "positive | negative | neutral",
      "score_impact": 0,
      "evidence": ["short RFP or knowledge-base evidence"]
    }}
  ],
  "checklist": [
    {{
      "id": "snake_case_id",
      "category": "scope | technical | delivery | commercial | risk | legal | documents",
      "label": "RFP information requirement",
      "description": "what the RFP should contain",
      "status": "present | partial | missing | not_applicable",
      "severity": "critical | high | medium | low",
      "evidence": ["short evidence from the RFP if present"],
      "follow_up": "clarification request when partial or missing, otherwise null"
    }}
  ],
  "missing_information": [
    {{
      "requirement_id": "matching checklist id",
      "category": "same category",
      "label": "missing or partial item",
      "severity": "critical | high | medium | low",
      "status": "partial | missing",
      "requested_action": "specific clarification question or requested document"
    }}
  ],
  "client_submission_checklist": [
    {{
      "id": "snake_case_id",
      "category": "corporate | financial | legal | compliance | security | hr | delivery | pricing | references | documents",
      "label": "material we must provide to the client",
      "description": "what needs to be prepared or submitted",
      "status": "required | conditional | optional | needs_review",
      "severity": "critical | high | medium | low",
      "responsible_team": "team likely responsible, or null",
      "evidence": ["short evidence from the RFP"],
      "requested_action": "specific internal action to prepare the item"
    }}
  ]
}}

For client_submission_checklist, include proposal deliverables and supporting evidence the vendor must
provide to the buyer. Examples include company credit rating, financial statements, employee criminal
background checks, employee credit checks, security questionnaires, insurance certificates, data
processing agreement, certifications, references, resumes, implementation plan, architecture diagrams,
pricing workbook, and signed forms. Include credit-rating or background-check items when the RFP asks
for them directly or implies them through vendor due diligence.

Unified knowledge base:
{_knowledge_context(knowledge_chunks)}

RFP text:
{_compact(rfp_text, MAX_RFP_CONTEXT_CHARS)}
""".strip()


def _parse_json_object(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RfpAssessmentUnavailable("OpenAI RFP assessment returned invalid JSON") from exc


def assess_rfp_text(
    rfp_text: str,
    knowledge_chunks: list[KnowledgeChunk] | None = None,
) -> AssessmentDraft:
    """Assess bid fit and RFP checklists using OpenAI and the unified knowledge base."""
    chunks = knowledge_chunks or []
    if not settings.openai_api_key:
        raise RfpAssessmentUnavailable(
            "OPENAI_API_KEY is required for RFP assessment; deterministic fallback is disabled"
        )
    if not chunks:
        raise RfpAssessmentUnavailable("No knowledge base chunks available for RFP assessment")

    completion = _openai_client().chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior proposal operations analyst. You inspect RFPs against "
                    "a company knowledge base and return strict JSON only."
                ),
            },
            {"role": "user", "content": _assessment_prompt(rfp_text, chunks)},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=3500,
    )

    content = completion.choices[0].message.content or ""
    try:
        return AssessmentDraft.model_validate(_parse_json_object(content))
    except ValidationError as exc:
        raise RfpAssessmentUnavailable(
            "OpenAI RFP assessment did not match the expected contract"
        ) from exc


def _latest_rfp_document(project_id: str, db: Session) -> DocumentRecord | None:
    return db.scalars(
        select(DocumentRecord)
        .where(
            DocumentRecord.project_id == project_id,
            DocumentRecord.document_type == DocumentType.rfp.value,
        )
        .order_by(DocumentRecord.created_at.desc())
    ).first()


def has_rfp_document(project_id: str, db: Session) -> bool:
    return _latest_rfp_document(project_id, db) is not None


def shared_knowledge_chunks(db: Session) -> list[KnowledgeChunk]:
    """Return the unified knowledge base used by every proposal project."""
    records = db.scalars(
        select(KnowledgeChunkRecord)
        .join(DocumentRecord)
        .where(DocumentRecord.document_type == DocumentType.knowledge.value)
        .order_by(KnowledgeChunkRecord.document_title, KnowledgeChunkRecord.chunk_index)
    ).all()
    return [record.to_schema() for record in records]


def assess_project_rfp(project_id: str, db: Session) -> RfpAssessment:
    """Create or update the latest RFP assessment for a project."""
    rfp_document = _latest_rfp_document(project_id, db)
    if not rfp_document or not rfp_document.extracted_text:
        raise RfpAssessmentUnavailable("No processed RFP document available for project")

    draft = assess_rfp_text(
        rfp_text=rfp_document.extracted_text,
        knowledge_chunks=shared_knowledge_chunks(db),
    )
    now = utc_now()
    existing = db.scalars(
        select(RfpAssessmentRecord).where(RfpAssessmentRecord.project_id == project_id)
    ).first()

    payload = {
        "rfp_document_id": rfp_document.id,
        "recommendation": draft.recommendation.value,
        "bid_score": draft.bid_score,
        "confidence": draft.confidence,
        "summary": draft.summary,
        "policy_source_documents": draft.policy_source_documents,
        "bid_factors": [factor.model_dump(mode="json") for factor in draft.bid_factors],
        "checklist": [item.model_dump(mode="json") for item in draft.checklist],
        "missing_information": [
            item.model_dump(mode="json") for item in draft.missing_information
        ],
        "client_submission_checklist": [
            item.model_dump(mode="json") for item in draft.client_submission_checklist
        ],
        "updated_at": now,
    }

    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        assessment = existing
    else:
        assessment = RfpAssessmentRecord(
            id=new_id("assessment"),
            project_id=project_id,
            generated_at=now,
            **payload,
        )
        db.add(assessment)

    db.flush()
    return assessment.to_schema()


def serialize_assessment_draft(draft: AssessmentDraft) -> dict:
    """Small helper for eval scripts and future tests."""
    return draft.model_dump(mode="json")
