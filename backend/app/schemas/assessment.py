from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BidRecommendation(StrEnum):
    bid = "bid"
    no_bid = "no_bid"
    needs_review = "needs_review"


class BidFactorSentiment(StrEnum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class RequirementCheckStatus(StrEnum):
    present = "present"
    partial = "partial"
    missing = "missing"
    not_applicable = "not_applicable"


class RequirementSeverity(StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class SubmissionRequirementStatus(StrEnum):
    required = "required"
    conditional = "conditional"
    optional = "optional"
    needs_review = "needs_review"


class BidFactor(BaseModel):
    id: str
    label: str
    sentiment: BidFactorSentiment
    score_impact: int
    evidence: list[str] = Field(default_factory=list)


class RfpChecklistItem(BaseModel):
    id: str
    category: str
    label: str
    description: str
    status: RequirementCheckStatus
    severity: RequirementSeverity
    evidence: list[str] = Field(default_factory=list)
    follow_up: str | None = None


class MissingInfoItem(BaseModel):
    requirement_id: str
    category: str
    label: str
    severity: RequirementSeverity
    status: RequirementCheckStatus
    requested_action: str


class ClientSubmissionItem(BaseModel):
    id: str
    category: str
    label: str
    description: str
    status: SubmissionRequirementStatus
    severity: RequirementSeverity
    responsible_team: str | None = None
    evidence: list[str] = Field(default_factory=list)
    requested_action: str


class RfpAssessment(BaseModel):
    id: str
    project_id: str
    rfp_document_id: str
    recommendation: BidRecommendation
    bid_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    summary: str
    policy_source_documents: list[str] = Field(default_factory=list)
    bid_factors: list[BidFactor] = Field(default_factory=list)
    checklist: list[RfpChecklistItem] = Field(default_factory=list)
    missing_information: list[MissingInfoItem] = Field(default_factory=list)
    client_submission_checklist: list[ClientSubmissionItem] = Field(default_factory=list)
    generated_at: datetime
    updated_at: datetime
