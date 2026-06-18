from enum import StrEnum

from pydantic import BaseModel


class QuestionStatus(StrEnum):
    pending = "pending"
    drafted = "drafted"
    approved = "approved"
    flagged = "flagged"


class QuestionCategory(StrEnum):
    general = "general"
    technical = "technical"
    security = "security"
    legal = "legal"
    pricing = "pricing"
    implementation = "implementation"
    support = "support"
    compliance = "compliance"
    experience = "experience"


class RfpQuestion(BaseModel):
    id: str
    project_id: str
    question_text: str
    category: QuestionCategory
    source_section: str | None = None
    source_text: str | None = None
    order_index: int
    status: QuestionStatus
