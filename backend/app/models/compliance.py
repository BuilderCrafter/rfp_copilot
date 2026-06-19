from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.schemas.compliance import (
    ComplianceIssue,
    ComplianceReportStatus,
    ComplianceSummary,
    RfpComplianceReport,
)


class RfpComplianceReportRecord(Base):
    __tablename__ = "rfp_compliance_reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        index=True,
        unique=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_schema(self) -> RfpComplianceReport:
        return RfpComplianceReport(
            id=self.id,
            project_id=self.project_id,
            status=ComplianceReportStatus(self.status),
            summary_text=self.summary_text,
            summary=ComplianceSummary(**self.summary),
            issues=[ComplianceIssue(**item) for item in self.issues or []],
            generated_at=self.generated_at,
            updated_at=self.updated_at,
        )
