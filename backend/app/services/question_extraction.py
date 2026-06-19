import json
import logging
from dataclasses import dataclass

from openai import OpenAI

from app.config import settings
from app.schemas.question import QuestionCategory

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {c.value for c in QuestionCategory}

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
        logger.warning("OPENAI_API_KEY not set — falling back to empty extraction.")
        return []

    client_kwargs: dict = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url
    client = OpenAI(**client_kwargs)

    print(f"\n[OpenAI] Extracting requirements from RFP ({len(text)} chars) using model '{settings.openai_model}'...\n", flush=True)

    completion = client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"RFP document:\n\n{text}"},
        ],
        temperature=0,
    )

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
    return candidates
