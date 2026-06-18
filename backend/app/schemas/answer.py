from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class AnswerStatus(StrEnum):
    not_started = "not_started"
    drafted = "drafted"
    edited = "edited"
    approved = "approved"
    flagged = "flagged"
    rejected = "rejected"


class Answer(BaseModel):
    id: str
    question_id: str
    draft_text: str
    final_text: str
    status: AnswerStatus
    review_note: str | None = None
    warning: str | None = None
    created_at: datetime
    updated_at: datetime


class AnswerUpdate(BaseModel):
    final_text: str
    review_note: str | None = None


class AnswerFlagRequest(BaseModel):
    review_note: str | None = None


class Citation(BaseModel):
    id: str
    answer_id: str
    chunk_id: str
    document_title: str
    section_title: str | None = None
    page_number: int | None = None
    excerpt: str
    relevance_score: float | None = None


class QuestionAnswerBundle(BaseModel):
    question_id: str
    question_text: str
    answer: Answer
    citations: list[Citation]
