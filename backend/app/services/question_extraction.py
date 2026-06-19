import json
import logging
import re
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

from app.config import settings
from app.schemas.question import QuestionCategory

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {c.value for c in QuestionCategory}
REQUIREMENT_PREFIX_PATTERN = re.compile(
    r"^\s*(?:[-*]\s+|(?:\d+(?:\.\d+)+|[A-Za-z]\)|\([A-Za-z0-9]+\))\s+)(?P<text>.+)"
)
RESPONSE_KEYWORDS = (
    "describe",
    "explain",
    "provide",
    "include",
    "propose",
    "demonstrate",
    "identify",
    "confirm",
    "submit",
    "detail",
    "outline",
    "vendor must",
    "vendor shall",
    "solution must",
    "solution shall",
)

_SYSTEM_PROMPT = """\
You are an expert RFP analyst. Given the full text of a Request for Proposal (RFP) document, \
extract every distinct requirement or question that a vendor must respond to.

Rules:
- Extract each requirement verbatim — do not paraphrase, summarise, or merge items.
- Include numbered items, lettered items, and direct questions.
- Ignore headings, preamble, and pure narrative that requires no vendor response.
- Sort the extracted requirements by their natural section order in the document.
- Assign each requirement exactly one category from this list:
    general, technical, security, legal, pricing, implementation, support, compliance, experience
- Identify the section heading the requirement belongs to (e.g. "3. Functional Requirements").

Return ONLY a JSON array. Each element must have exactly these keys:
  "text"            — the requirement exactly as it appears in the document
  "category"        — one value from the category list above
  "source_section"  — the section heading string, or null if none
"""


@dataclass(frozen=True)
class QuestionCandidate:
    question_text: str
    category: QuestionCategory
    source_section: str | None
    source_text: str | None


def _infer_category(text: str, section: str | None) -> QuestionCategory:
    haystack = f"{section or ''} {text}".lower()
    if any(token in haystack for token in ("security", "privacy", "gdpr", "compliance", "audit")):
        if "compliance" in haystack or "audit" in haystack:
            return QuestionCategory.compliance
        return QuestionCategory.security
    if any(token in haystack for token in ("price", "pricing", "commercial", "cost", "fee")):
        return QuestionCategory.pricing
    if any(token in haystack for token in ("timeline", "implementation", "project plan", "delivery")):
        return QuestionCategory.implementation
    if any(token in haystack for token in ("support", "sla", "incident", "service desk")):
        return QuestionCategory.support
    if any(token in haystack for token in ("experience", "reference", "case stud")):
        return QuestionCategory.experience
    if any(token in haystack for token in ("legal", "contract", "terms")):
        return QuestionCategory.legal
    if any(token in haystack for token in ("technical", "integration", "api", "architecture", "data")):
        return QuestionCategory.technical
    return QuestionCategory.general


def _fallback_extract_questions(text: str) -> list[QuestionCandidate]:
    """Extract common numbered RFP response items when LLM extraction is unavailable."""
    candidates: list[QuestionCandidate] = []
    seen: set[str] = set()
    current_section: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            current_section = line.lstrip("#").strip()
            continue

        match = REQUIREMENT_PREFIX_PATTERN.match(line)
        if match:
            requirement_text = match.group("text").strip()
        elif "?" in line or any(keyword in line.lower() for keyword in RESPONSE_KEYWORDS):
            requirement_text = line
        else:
            continue

        if len(requirement_text) < 20:
            continue

        normalized = " ".join(requirement_text.lower().split())
        if normalized in seen:
            continue
        seen.add(normalized)

        candidates.append(
            QuestionCandidate(
                question_text=requirement_text,
                category=_infer_category(requirement_text, current_section),
                source_section=current_section,
                source_text=requirement_text,
            )
        )

    return candidates


def _parse_category(raw: str) -> QuestionCategory:
    value = raw.strip().lower()
    if value in VALID_CATEGORIES:
        return QuestionCategory(value)
    return QuestionCategory.general


def extract_questions_from_text(
    project_id_or_document_text: str,
    document_text: str | None = None,
) -> list[QuestionCandidate]:
    text = document_text if document_text is not None else project_id_or_document_text

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set — falling back to deterministic extraction.")
        return _fallback_extract_questions(text)

    client_kwargs: dict = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url
    client = OpenAI(**client_kwargs)

    print(f"\n[OpenAI] Extracting requirements from RFP ({len(text)} chars) using model '{settings.openai_model}'...\n", flush=True)

    try:
        completion = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"RFP document:\n\n{text}"},
            ],
            temperature=0,
        )
    except OpenAIError:
        logger.exception("OpenAI requirement extraction failed; using deterministic fallback.")
        return _fallback_extract_questions(text)

    raw_content = completion.choices[0].message.content or "{}"

    try:
        parsed = json.loads(raw_content)
        # Model may wrap the array in an object key
        if isinstance(parsed, dict):
            items = next(
                (v for v in parsed.values() if isinstance(v, list)),
                [],
            )
        else:
            items = parsed
    except json.JSONDecodeError:
        logger.error("OpenAI returned invalid JSON for requirement extraction.")
        return []

    candidates: list[QuestionCandidate] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("text"):
            continue
        candidates.append(
            QuestionCandidate(
                question_text=item["text"].strip(),
                category=_parse_category(item.get("category", "general")),
                source_section=item.get("source_section") or None,
                source_text=item["text"].strip(),
            )
        )

    print(f"[OpenAI] Extracted {len(candidates)} requirements.\n", flush=True)
    if not candidates:
        logger.warning("OpenAI returned no requirements; using deterministic fallback.")
        return _fallback_extract_questions(text)

    return candidates
