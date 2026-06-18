from fastapi import APIRouter, HTTPException

from app.schemas.common import new_id
from app.schemas.document import DocumentType
from app.schemas.question import QuestionStatus, RfpQuestion
from app.services.question_extraction import extract_questions_from_text
from app.storage.memory_store import store

router = APIRouter(prefix="/projects/{project_id}", tags=["questions"])


def _ensure_project(project_id: str) -> None:
    if project_id not in store.projects:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/extract_questions", response_model=list[RfpQuestion])
def extract_questions(project_id: str) -> list[RfpQuestion]:
    """Extract answerable questions/requirements from the project's RFP document."""
    _ensure_project(project_id)
    rfp_docs = [
        document
        for document in store.documents.values()
        if document.project_id == project_id and document.document_type == DocumentType.rfp
    ]
    if not rfp_docs:
        raise HTTPException(status_code=400, detail="No RFP document uploaded for project")

    rfp_doc = rfp_docs[-1]
    text = store.document_texts.get(rfp_doc.id, "")
    candidates = extract_questions_from_text(text)

    created: list[RfpQuestion] = []
    for index, candidate in enumerate(candidates):
        question = RfpQuestion(
            id=new_id("question"),
            project_id=project_id,
            question_text=candidate.question_text,
            category=candidate.category,
            source_section=candidate.source_section,
            source_text=candidate.source_text,
            order_index=index,
            status=QuestionStatus.pending,
        )
        store.questions[question.id] = question
        created.append(question)

    return created


@router.get("/questions", response_model=list[RfpQuestion])
def list_questions(project_id: str) -> list[RfpQuestion]:
    """List extracted questions for a project."""
    _ensure_project(project_id)
    return sorted(
        [question for question in store.questions.values() if question.project_id == project_id],
        key=lambda q: q.order_index,
    )
