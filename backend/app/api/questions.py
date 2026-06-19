from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import DocumentRecord, ProjectRecord, RfpQuestionRecord
from app.schemas.common import new_id
from app.schemas.document import DocumentStatus, DocumentType
from app.schemas.question import QuestionStatus, RfpQuestion
from app.services.question_extraction import extract_questions_from_text

router = APIRouter(prefix="/projects/{project_id}", tags=["questions"])
DbSession = Annotated[Session, Depends(get_db)]


def _ensure_project(project_id: str, db: Session) -> None:
    if not db.get(ProjectRecord, project_id):
        raise HTTPException(status_code=404, detail="Project not found")


def _remove_existing_project_questions(project_id: str, db: Session) -> None:
    """Make extraction repeatable for the frontend by replacing the prior question set."""
    questions = db.scalars(
        select(RfpQuestionRecord).where(RfpQuestionRecord.project_id == project_id)
    ).all()
    for question in questions:
        db.delete(question)


@router.post("/extract_questions", response_model=list[RfpQuestion], operation_id="extract_questions")
def extract_questions(project_id: str, db: DbSession) -> list[RfpQuestion]:
    """Extract answerable questions/requirements from the project's RFP document."""
    _ensure_project(project_id, db)
    rfp_doc = db.scalars(
        select(DocumentRecord)
        .where(
            DocumentRecord.project_id == project_id,
            DocumentRecord.document_type == DocumentType.rfp.value,
        )
        .order_by(DocumentRecord.created_at.desc())
    ).first()
    if not rfp_doc:
        raise HTTPException(status_code=400, detail="No RFP document uploaded for project")

    if rfp_doc.status != DocumentStatus.processed.value or not rfp_doc.extracted_text:
        raise HTTPException(
            status_code=409,
            detail="RFP document is still processing. Try extracting requirements again in a moment.",
        )

    text = rfp_doc.extracted_text
    candidates = extract_questions_from_text(project_id, text)

    _remove_existing_project_questions(project_id, db)
    created: list[RfpQuestionRecord] = []
    for index, candidate in enumerate(candidates):
        question = RfpQuestionRecord(
            id=new_id("question"),
            project_id=project_id,
            question_text=candidate.question_text,
            category=candidate.category.value,
            source_section=candidate.source_section,
            source_text=candidate.source_text,
            order_index=index,
            status=QuestionStatus.pending.value,
        )
        db.add(question)
        created.append(question)

    db.commit()
    return [question.to_schema() for question in created]


@router.get("/questions", response_model=list[RfpQuestion], operation_id="list_questions")
def list_questions(project_id: str, db: DbSession) -> list[RfpQuestion]:
    """List extracted questions for a project."""
    _ensure_project(project_id, db)
    questions = db.scalars(
        select(RfpQuestionRecord)
        .where(RfpQuestionRecord.project_id == project_id)
        .order_by(RfpQuestionRecord.order_index)
    ).all()
    return [question.to_schema() for question in questions]
