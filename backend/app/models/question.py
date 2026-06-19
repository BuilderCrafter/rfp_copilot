from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.question import QuestionCategory, QuestionStatus, RfpQuestion

if TYPE_CHECKING:
    from app.models.answer import AnswerRecord
    from app.models.project import ProjectRecord


class RfpQuestionRecord(Base):
    __tablename__ = "rfp_questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    source_section: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    project: Mapped["ProjectRecord"] = relationship(back_populates="questions")
    answer: Mapped["AnswerRecord | None"] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )

    def to_schema(self) -> RfpQuestion:
        return RfpQuestion(
            id=self.id,
            project_id=self.project_id,
            question_text=self.question_text,
            category=QuestionCategory(self.category),
            source_section=self.source_section,
            source_text=self.source_text,
            order_index=self.order_index,
            status=QuestionStatus(self.status),
        )
