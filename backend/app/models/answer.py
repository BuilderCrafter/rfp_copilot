from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.answer import Answer, AnswerStatus, Citation

if TYPE_CHECKING:
    from app.models.question import RfpQuestionRecord


class AnswerRecord(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    question_id: Mapped[str] = mapped_column(
        ForeignKey("rfp_questions.id"),
        unique=True,
        index=True,
        nullable=False,
    )
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    final_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    question: Mapped["RfpQuestionRecord"] = relationship(back_populates="answer")
    citations: Mapped[list["CitationRecord"]] = relationship(
        back_populates="answer",
        cascade="all, delete-orphan",
    )

    def to_schema(self) -> Answer:
        return Answer(
            id=self.id,
            question_id=self.question_id,
            draft_text=self.draft_text,
            final_text=self.final_text,
            status=AnswerStatus(self.status),
            review_note=self.review_note,
            warning=self.warning,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class CitationRecord(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    answer_id: Mapped[str] = mapped_column(ForeignKey("answers.id"), index=True, nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(64), nullable=False)
    document_title: Mapped[str] = mapped_column(String(512), nullable=False)
    section_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    answer: Mapped[AnswerRecord] = relationship(back_populates="citations")

    def to_schema(self) -> Citation:
        return Citation(
            id=self.id,
            answer_id=self.answer_id,
            chunk_id=self.chunk_id,
            document_title=self.document_title,
            section_title=self.section_title,
            page_number=self.page_number,
            excerpt=self.excerpt,
            relevance_score=self.relevance_score,
        )
