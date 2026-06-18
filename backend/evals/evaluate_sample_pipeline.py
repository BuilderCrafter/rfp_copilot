"""Run qualitative pipeline evaluations against the sample RFP/knowledge data.

This is not a traditional unit-test suite. It is a fast review tool for the team to see
whether the MVP pipeline extracts useful questions, retrieves relevant source material,
and drafts answers with citations.

Usage from backend/:
    python evals/evaluate_sample_pipeline.py

Usage from repo root:
    make eval
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# Allow running this file directly from backend/ without installing the package first.
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.document import KnowledgeChunk  # noqa: E402
from app.services.answer_generation import draft_answer_from_sources  # noqa: E402
from app.services.knowledge_ingestion import chunk_knowledge_document  # noqa: E402
from app.services.question_extraction import extract_questions_from_text  # noqa: E402
from app.services.retrieval import retrieve_relevant_chunks  # noqa: E402

DEFAULT_RFP = REPO_ROOT / "sample_data" / "rfps" / "01_smart_city_citizen_services_rfp.md"
DEFAULT_KB_DIR = REPO_ROOT / "sample_data" / "knowledge_base"
REPORT_DIR = BACKEND_DIR / "evals" / "reports"
SUPPORTED_TEXT_SUFFIXES = {".md", ".txt"}


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def iter_knowledge_files(kb_dir: Path) -> Iterable[Path]:
    for path in sorted(kb_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_TEXT_SUFFIXES:
            yield path


def build_knowledge_chunks(kb_dir: Path) -> list[KnowledgeChunk]:
    """Chunk all knowledge documents into the same shape used by retrieval."""
    chunks: list[KnowledgeChunk] = []
    for doc_index, path in enumerate(iter_knowledge_files(kb_dir), start=1):
        document_id = f"eval_doc_{doc_index:03d}"
        document_title = path.stem.replace("_", " ").title()
        text = read_text_file(path)
        candidates = chunk_knowledge_document(
            document_id=document_id,
            document_title=document_title,
            text=text,
            chunk_size=900,
            chunk_overlap=120,
        )
        for candidate in candidates:
            chunks.append(KnowledgeChunk(**asdict(candidate)))
    return chunks


def evaluate_pipeline(
    rfp_path: Path,
    kb_dir: Path,
    max_questions: int,
    top_k: int,
    min_score: float,
) -> dict:
    rfp_text = read_text_file(rfp_path)
    questions = extract_questions_from_text(rfp_text)
    chunks = build_knowledge_chunks(kb_dir)

    items = []
    for index, question in enumerate(questions[:max_questions], start=1):
        retrieved = retrieve_relevant_chunks(
            question_text=question.question_text,
            chunks=chunks,
            top_k=top_k,
            min_score=min_score,
        )
        draft = draft_answer_from_sources(question.question_text, retrieved)
        items.append(
            {
                "index": index,
                "question_text": question.question_text,
                "category": str(question.category),
                "source_section": question.source_section,
                "draft_text": draft.draft_text,
                "warning": draft.warning,
                "citations": [asdict(citation) for citation in draft.citations],
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rfp_file": str(rfp_path.relative_to(REPO_ROOT)),
        "knowledge_base_dir": str(kb_dir.relative_to(REPO_ROOT)),
        "question_count_detected": len(questions),
        "question_count_evaluated": len(items),
        "knowledge_chunk_count": len(chunks),
        "items": items,
    }


def write_reports(result: dict, output_stem: str) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / f"{output_stem}.json"
    md_path = REPORT_DIR / f"{output_stem}.md"

    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append(f"# Pipeline Eval Report: {result['rfp_file']}")
    lines.append("")
    lines.append(f"Generated at: `{result['generated_at']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- RFP file: `{result['rfp_file']}`")
    lines.append(f"- Knowledge base: `{result['knowledge_base_dir']}`")
    lines.append(f"- Questions detected: {result['question_count_detected']}")
    lines.append(f"- Questions evaluated: {result['question_count_evaluated']}")
    lines.append(f"- Knowledge chunks: {result['knowledge_chunk_count']}")
    lines.append("")
    lines.append("## Questions, Drafts, and Citations")
    lines.append("")

    for item in result["items"]:
        lines.append(f"### {item['index']}. {item['question_text']}")
        lines.append("")
        lines.append(f"Category: `{item['category']}`")
        if item.get("source_section"):
            lines.append(f"Source section: `{item['source_section']}`")
        if item.get("warning"):
            lines.append(f"Warning: **{item['warning']}**")
        lines.append("")
        lines.append("#### Draft answer")
        lines.append("")
        lines.append(item["draft_text"])
        lines.append("")
        lines.append("#### Citations")
        lines.append("")
        if not item["citations"]:
            lines.append("No citations returned.")
        else:
            for citation in item["citations"]:
                title = citation["document_title"]
                score = citation.get("relevance_score")
                excerpt = citation["excerpt"]
                lines.append(f"- **{title}** | score: `{score}`")
                lines.append(f"  - {excerpt}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run qualitative sample RFP pipeline evaluation.")
    parser.add_argument("--rfp", type=Path, default=DEFAULT_RFP, help="Path to sample RFP file")
    parser.add_argument("--kb_dir", type=Path, default=DEFAULT_KB_DIR, help="Knowledge base directory")
    parser.add_argument("--max_questions", type=int, default=12, help="Max questions to evaluate")
    parser.add_argument("--top_k", type=int, default=5, help="Number of retrieved chunks per question")
    parser.add_argument("--min_score", type=float, default=0.03, help="Minimum lexical relevance score")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rfp_path = args.rfp.resolve()
    kb_dir = args.kb_dir.resolve()

    if not rfp_path.exists():
        print(f"RFP file not found: {rfp_path}", file=sys.stderr)
        return 2
    if not kb_dir.exists():
        print(f"Knowledge base dir not found: {kb_dir}", file=sys.stderr)
        return 2

    result = evaluate_pipeline(
        rfp_path=rfp_path,
        kb_dir=kb_dir,
        max_questions=args.max_questions,
        top_k=args.top_k,
        min_score=args.min_score,
    )
    output_stem = f"{rfp_path.stem}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    json_path, md_path = write_reports(result, output_stem)

    warnings = sum(1 for item in result["items"] if item.get("warning"))
    cited = sum(1 for item in result["items"] if item.get("citations"))

    print("Pipeline eval completed.")
    print(f"RFP: {result['rfp_file']}")
    print(f"Questions detected: {result['question_count_detected']}")
    print(f"Questions evaluated: {result['question_count_evaluated']}")
    print(f"Answers with citations: {cited}")
    print(f"Warnings / unsupported answers: {warnings}")
    print(f"Markdown report: {md_path.relative_to(BACKEND_DIR)}")
    print(f"JSON report: {json_path.relative_to(BACKEND_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
