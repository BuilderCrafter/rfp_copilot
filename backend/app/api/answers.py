from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.answer import (
    Answer,
    AnswerFlagRequest,
    AnswerStatus,
    AnswerUpdate,
    Citation,
    QuestionAnswerBundle,
)
from app.schemas.common import new_id, utc_now
from app.schemas.question import QuestionStatus
from app.services.answer_generation import draft_answer_from_sources
from app.services.retrieval import retrieve_relevant_chunks
from app.storage.memory_store import store

router = APIRouter(tags=["answers"])


def _get_answer(answer_id: str) -> Answer:
    answer = store.answers.get(answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer


def _bundle_for_question(question_id: str) -> QuestionAnswerBundle:
    question = store.questions.get(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = next((a for a in store.answers.values() if a.question_id == question_id), None)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found for question")

    citations = [citation for citation in store.citations.values() if citation.answer_id == answer.id]
    return QuestionAnswerBundle(
        question_id=question.id,
        question_text=question.question_text,
        answer=answer,
        citations=citations,
    )


@router.post("/questions/{question_id}/draft_answer", response_model=QuestionAnswerBundle)
def draft_answer(question_id: str) -> QuestionAnswerBundle:
    """Generate or regenerate a draft answer for one question."""
    question = store.questions.get(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    project_chunks = [
        chunk
        for chunk in store.chunks.values()
        if store.documents[chunk.document_id].project_id == question.project_id
    ]
    retrieved = retrieve_relevant_chunks(
        question_text=question.question_text,
        chunks=project_chunks,
        top_k=settings.rag_top_k,
    )
    result = draft_answer_from_sources(question.question_text, retrieved)

    now = utc_now()
    existing = next((a for a in store.answers.values() if a.question_id == question.id), None)
    answer_id = existing.id if existing else new_id("answer")
    status = AnswerStatus.flagged if result.warning else AnswerStatus.drafted

    answer = Answer(
        id=answer_id,
        question_id=question.id,
        draft_text=result.draft_text,
        final_text=result.draft_text,
        status=status,
        review_note=None,
        warning=result.warning,
        created_at=existing.created_at if existing else now,
        updated_at=now,
    )
    store.answers[answer.id] = answer

    # Remove old citations for regenerated answers.
    for citation_id, citation in list(store.citations.items()):
        if citation.answer_id == answer.id:
            del store.citations[citation_id]

    citations: list[Citation] = []
    for candidate in result.citations:
        citation = Citation(
            id=new_id("citation"),
            answer_id=answer.id,
            chunk_id=candidate.chunk_id,
            document_title=candidate.document_title,
            section_title=candidate.section_title,
            page_number=candidate.page_number,
            excerpt=candidate.excerpt,
            relevance_score=candidate.relevance_score,
        )
        store.citations[citation.id] = citation
        citations.append(citation)

    question_status = QuestionStatus.flagged if result.warning else QuestionStatus.drafted
    store.questions[question.id] = question.model_copy(update={"status": question_status})

    return QuestionAnswerBundle(
        question_id=question.id,
        question_text=question.question_text,
        answer=answer,
        citations=citations,
    )


@router.get("/questions/{question_id}/answer", response_model=QuestionAnswerBundle)
def get_question_answer(question_id: str) -> QuestionAnswerBundle:
    """Return the answer and citations for a question."""
    return _bundle_for_question(question_id)


@router.patch("/answers/{answer_id}", response_model=Answer)
def update_answer(answer_id: str, payload: AnswerUpdate) -> Answer:
    """Update reviewer-controlled final text and mark the answer as edited."""
    answer = _get_answer(answer_id)
    updated = answer.model_copy(
        update={
            "final_text": payload.final_text,
            "review_note": payload.review_note,
            "status": AnswerStatus.edited,
            "updated_at": utc_now(),
        }
    )
    store.answers[answer_id] = updated
    return updated


@router.post("/answers/{answer_id}/approve", response_model=Answer)
def approve_answer(answer_id: str) -> Answer:
    """Mark an answer as approved for export."""
    answer = _get_answer(answer_id)
    updated = answer.model_copy(update={"status": AnswerStatus.approved, "updated_at": utc_now()})
    store.answers[answer_id] = updated

    question = store.questions.get(answer.question_id)
    if question:
        store.questions[question.id] = question.model_copy(update={"status": QuestionStatus.approved})
    return updated


@router.post("/answers/{answer_id}/flag", response_model=Answer)
def flag_answer(answer_id: str, payload: AnswerFlagRequest | None = None) -> Answer:
    """Flag an answer for additional human review."""
    answer = _get_answer(answer_id)
    updated = answer.model_copy(
        update={
            "status": AnswerStatus.flagged,
            "review_note": payload.review_note if payload else answer.review_note,
            "updated_at": utc_now(),
        }
    )
    store.answers[answer_id] = updated

    question = store.questions.get(answer.question_id)
    if question:
        store.questions[question.id] = question.model_copy(update={"status": QuestionStatus.flagged})
    return updated


@router.post("/answers/{answer_id}/reject", response_model=Answer)
def reject_answer(answer_id: str) -> Answer:
    """Reject an answer so it is excluded from export."""
    answer = _get_answer(answer_id)
    updated = answer.model_copy(update={"status": AnswerStatus.rejected, "updated_at": utc_now()})
    store.answers[answer_id] = updated
    return updated
