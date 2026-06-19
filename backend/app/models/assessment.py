from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.schemas.assessment import (
    BidFactor,
    BidRecommendation,
    ClientSubmissionItem,
    MissingInfoItem,
    RfpAssessment,
    RfpChecklistItem,
)


class RfpAssessmentRecord(Base):
    __tablename__ = "rfp_assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        index=True,
        unique=True,
        nullable=False,
    )
    rfp_document_id: Mapped[str] = mapped_column(String(64), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(32), nullable=False)
    bid_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    policy_source_documents: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    bid_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    checklist: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    missing_information: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    client_submission_checklist: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_schema(self) -> RfpAssessment:
        return RfpAssessment(
            id=self.id,
            project_id=self.project_id,
            rfp_document_id=self.rfp_document_id,
            recommendation=BidRecommendation(self.recommendation),
            bid_score=self.bid_score,
            confidence=self.confidence,
            summary=self.summary,
            policy_source_documents=list(self.policy_source_documents or []),
            bid_factors=[BidFactor(**item) for item in self.bid_factors or []],
            checklist=[RfpChecklistItem(**item) for item in self.checklist or []],
            missing_information=[
                MissingInfoItem(**item) for item in self.missing_information or []
            ],
            client_submission_checklist=[
                ClientSubmissionItem(**item) for item in self.client_submission_checklist or []
            ],
            generated_at=self.generated_at,
            updated_at=self.updated_at,
        )
