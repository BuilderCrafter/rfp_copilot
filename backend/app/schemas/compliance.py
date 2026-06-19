from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ComplianceReportStatus(StrEnum):
    passed = "passed"
    warnings = "warnings"
    blocked = "blocked"


class ComplianceIssueSeverity(StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ComplianceIssueCategory(StrEnum):
    assessment_missing = "assessment_missing"
    assessment_needs_review = "assessment_needs_review"
    no_bid_recommendation = "no_bid_recommendation"
    rfp_missing = "rfp_missing"
    requirements_not_extracted = "requirements_not_extracted"
    unanswered_requirement = "unanswered_requirement"
    unapproved_answer = "unapproved_answer"
    flagged_answer = "flagged_answer"
    rejected_answer = "rejected_answer"
    uncited_answer = "uncited_answer"
    missing_rfp_information = "missing_rfp_information"
    submission_item_open = "submission_item_open"


class ComplianceIssue(BaseModel):
    id: str
    category: ComplianceIssueCategory
    severity: ComplianceIssueSeverity
    message: str
    recommended_action: str
    requirement_id: str | None = None
    answer_id: str | None = None
    assessment_item_id: str | None = None
    source: str | None = None


class ComplianceSummary(BaseModel):
    total_requirements: int
    answered_requirements: int
    approved_or_edited_answers: int
    drafted_answers: int
    flagged_answers: int
    rejected_answers: int
    missing_answers: int
    issues_by_severity: dict[str, int] = Field(default_factory=dict)


class RfpComplianceReport(BaseModel):
    id: str
    project_id: str
    status: ComplianceReportStatus
    summary_text: str
    summary: ComplianceSummary
    issues: list[ComplianceIssue] = Field(default_factory=list)
    generated_at: datetime
    updated_at: datetime
