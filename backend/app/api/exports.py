from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models import AnswerRecord, ProjectRecord, RfpQuestionRecord
from app.schemas.export import ExportResponse
from app.services.export_pdf import export_project_to_pdf

router = APIRouter(prefix="/projects/{project_id}", tags=["export"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/export", response_model=ExportResponse, operation_id="export_project")
def export_project(project_id: str, db: DbSession) -> ExportResponse:
    """Export approved/edited project answers to PDF."""
    project = db.get(ProjectRecord, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    question_records = db.scalars(
        select(RfpQuestionRecord)
        .where(RfpQuestionRecord.project_id == project_id)
        .order_by(RfpQuestionRecord.order_index)
    ).all()
    answer_records = db.scalars(
        select(AnswerRecord).where(
            AnswerRecord.question_id.in_([question.id for question in question_records])
        )
    ).all()
    questions = [question.to_schema() for question in question_records]
    answers_by_question_id = {
        answer.question_id: answer.to_schema() for answer in answer_records
    }

    filename = f"{project.id}_final_response.pdf"
    output_path = settings.export_dir / filename
    count = export_project_to_pdf(
        project_name=project.name,
        questions=questions,
        answers_by_question_id=answers_by_question_id,
        output_path=output_path,
    )
    return ExportResponse(download_url=f"/exports/{filename}", exported_answer_count=count)
