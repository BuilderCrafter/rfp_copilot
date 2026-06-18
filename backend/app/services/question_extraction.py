import re
from dataclasses import dataclass

from app.schemas.question import QuestionCategory


@dataclass(frozen=True)
class QuestionCandidate:
    question_text: str
    category: QuestionCategory
    source_section: str | None
    source_text: str | None


CATEGORY_KEYWORDS: list[tuple[QuestionCategory, tuple[str, ...]]] = [
    (QuestionCategory.security, ("security", "encryption", "access control", "audit", "privacy")),
    (QuestionCategory.compliance, ("gdpr", "iso", "compliance", "regulatory")),
    (QuestionCategory.support, ("support", "maintenance", "incident", "sla")),
    (QuestionCategory.implementation, ("implementation", "delivery", "methodology", "governance")),
    (QuestionCategory.experience, ("experience", "similar projects", "case study", "reference")),
    (QuestionCategory.pricing, ("price", "pricing", "cost", "commercial")),
    (QuestionCategory.legal, ("legal", "contract", "liability", "terms")),
    (QuestionCategory.technical, ("architecture", "integration", "api", "technical")),
]


def categorize_question(text: str) -> QuestionCategory:
    """Assign a simple MVP category based on keywords."""
    lowered = text.lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return category
    return QuestionCategory.general


def extract_questions_from_text(document_text: str) -> list[QuestionCandidate]:
    """Extract answerable RFP questions/requirements using lightweight rules.

    This is deliberately simple and reliable for the first MVP. An LLM-based extractor
    can replace or augment this function later while keeping the same return shape.
    """
    candidates: list[QuestionCandidate] = []
    current_section: str | None = None

    for raw_line in document_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            current_section = line.lstrip("#").strip()
            continue

        looks_like_question = line.endswith("?")
        looks_like_requirement = bool(
            re.match(r"^(\d+\.\d+|\d+\)|[a-zA-Z]\))\s+", line)
            and any(
                phrase in line.lower()
                for phrase in ("describe", "explain", "provide", "must", "shall", "include")
            )
        )

        if looks_like_question or looks_like_requirement:
            normalized = re.sub(r"^(\d+\.\d+|\d+\)|[a-zA-Z]\))\s+", "", line).strip()
            candidates.append(
                QuestionCandidate(
                    question_text=normalized,
                    category=categorize_question(normalized),
                    source_section=current_section,
                    source_text=line,
                )
            )

    return candidates
