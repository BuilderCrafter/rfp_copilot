from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models import (
    AnswerRecord,
    CitationRecord,
    RfpQuestionRecord,
)
from app.schemas.answer import (
    Answer,
    AnswerFlagRequest,
    AnswerStatus,
    AnswerUpdate,
    QuestionAnswerBundle,
)
from app.schemas.common import ErrorResponse, new_id, utc_now
from app.schemas.question import QuestionStatus
from app.services.answer_generation import draft_answer_from_sources
from app.services.retrieval import retrieve_relevant_chunks
from app.services.rfp_assessment import shared_knowledge_chunks

router = APIRouter(tags=["answers"])
DbSession = Annotated[Session, Depends(get_db)]


def _get_answer_record(answer_id: str, db: Session) -> AnswerRecord:
    answer = db.get(AnswerRecord, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer


def _bundle_for_question(question_id: str, db: Session) -> QuestionAnswerBundle:
    question = db.get(RfpQuestionRecord, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = db.scalars(
        select(AnswerRecord).where(AnswerRecord.question_id == question_id)
    ).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found for question")

    citations = db.scalars(
        select(CitationRecord).where(CitationRecord.answer_id == answer.id)
    ).all()
    return QuestionAnswerBundle(
        question_id=question.id,
        question_text=question.question_text,
        answer=answer.to_schema(),
        citations=[citation.to_schema() for citation in citations],
    )


@router.post(
    "/questions/{question_id}/draft_answer",
    response_model=QuestionAnswerBundle,
    operation_id="draft_answer",
)
def draft_answer(question_id: str, db: DbSession) -> QuestionAnswerBundle:
    """Generate or regenerate a draft answer for one question."""
    question = db.get(RfpQuestionRecord, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    retrieved = retrieve_relevant_chunks(
        question_text=question.question_text,
        chunks=shared_knowledge_chunks(db),
        top_k=settings.rag_top_k,
    )
    result = draft_answer_from_sources(question.question_text, retrieved)

    now = utc_now()
    existing = db.scalars(
        select(AnswerRecord).where(AnswerRecord.question_id == question.id)
    ).first()
    status = AnswerStatus.flagged if result.warning else AnswerStatus.drafted

    if existing:
        answer = existing
        answer.draft_text = result.draft_text
        answer.final_text = result.draft_text
        answer.status = status.value
        answer.review_note = None
        answer.warning = result.warning
        answer.updated_at = now
    else:
        answer = AnswerRecord(
            id=new_id("answer"),
            question_id=question.id,
            draft_text=result.draft_text,
            final_text=result.draft_text,
            status=status.value,
            review_note=None,
            warning=result.warning,
            created_at=now,
            updated_at=now,
        )
        db.add(answer)
        db.flush()

    # Remove old citations for regenerated answers.
    for citation in db.scalars(
        select(CitationRecord).where(CitationRecord.answer_id == answer.id)
    ).all():
        db.delete(citation)

    citations: list[CitationRecord] = []
    for candidate in result.citations:
        citation = CitationRecord(
            id=new_id("citation"),
            answer_id=answer.id,
            chunk_id=candidate.chunk_id,
            document_title=candidate.document_title,
            section_title=candidate.section_title,
            page_number=candidate.page_number,
            excerpt=candidate.excerpt,
            relevance_score=candidate.relevance_score,
        )
        db.add(citation)
        citations.append(citation)

    question_status = QuestionStatus.flagged if result.warning else QuestionStatus.drafted
    question.status = question_status.value
    db.commit()

    return QuestionAnswerBundle(
        question_id=question.id,
        question_text=question.question_text,
        answer=answer.to_schema(),
        citations=[citation.to_schema() for citation in citations],
    )


@router.get(
    "/questions/{question_id}/answer",
    response_model=QuestionAnswerBundle,
    responses={404: {"model": ErrorResponse}},
    operation_id="get_question_answer",
)
def get_question_answer(question_id: str, db: DbSession) -> QuestionAnswerBundle:
    """Return the answer and citations for a question."""
    return _bundle_for_question(question_id, db)


@router.patch("/answers/{answer_id}", response_model=Answer, operation_id="update_answer")
def update_answer(answer_id: str, payload: AnswerUpdate, db: DbSession) -> Answer:
    """Update reviewer-controlled final text and mark the answer as edited."""
    answer = _get_answer_record(answer_id, db)
    answer.final_text = payload.final_text
    answer.review_note = payload.review_note
    answer.status = AnswerStatus.edited.value
    answer.updated_at = utc_now()
    db.commit()
    return answer.to_schema()


@router.post("/answers/{answer_id}/approve", response_model=Answer, operation_id="approve_answer")
def approve_answer(answer_id: str, db: DbSession) -> Answer:
    """Mark an answer as approved for export."""
    answer = _get_answer_record(answer_id, db)
    answer.status = AnswerStatus.approved.value
    answer.updated_at = utc_now()

    question = db.get(RfpQuestionRecord, answer.question_id)
    if question:
        question.status = QuestionStatus.approved.value
    db.commit()
    return answer.to_schema()


@router.post("/answers/{answer_id}/flag", response_model=Answer, operation_id="flag_answer")
def flag_answer(
    answer_id: str,
    db: DbSession,
    payload: AnswerFlagRequest | None = None,
) -> Answer:
    """Flag an answer for additional human review."""
    answer = _get_answer_record(answer_id, db)
    answer.status = AnswerStatus.flagged.value
    answer.review_note = payload.review_note if payload else answer.review_note
    answer.updated_at = utc_now()

    question = db.get(RfpQuestionRecord, answer.question_id)
    if question:
        question.status = QuestionStatus.flagged.value
    db.commit()
    return answer.to_schema()


@router.post("/answers/{answer_id}/reject", response_model=Answer, operation_id="reject_answer")
def reject_answer(answer_id: str, db: DbSession) -> Answer:
    """Reject an answer so it is excluded from export."""
    answer = _get_answer_record(answer_id, db)
    answer.status = AnswerStatus.rejected.value
    answer.updated_at = utc_now()
    db.commit()
    return answer.to_schema()
