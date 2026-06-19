from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.export import ExportResponse
from app.services.export_docx import export_project_to_docx
from app.storage.memory_store import store

router = APIRouter(prefix="/projects/{project_id}", tags=["export"])


@router.post("/export", response_model=ExportResponse, operation_id="export_project")
def export_project(project_id: str) -> ExportResponse:
    """Export approved/edited project answers to DOCX."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    questions = [question for question in store.questions.values() if question.project_id == project_id]
    answers_by_question_id = {answer.question_id: answer for answer in store.answers.values()}
    citations_by_answer_id = {
        answer.id: [citation for citation in store.citations.values() if citation.answer_id == answer.id]
        for answer in store.answers.values()
    }

    filename = f"{project.id}_final_response.docx"
    output_path = settings.export_dir / filename
    count = export_project_to_docx(
        project_name=project.name,
        questions=questions,
        answers_by_question_id=answers_by_question_id,
        citations_by_answer_id=citations_by_answer_id,
        output_path=output_path,
    )
    return ExportResponse(download_url=f"/exports/{filename}", exported_answer_count=count)
