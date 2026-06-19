from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models import DocumentRecord, KnowledgeChunkRecord, ProjectRecord
from app.schemas.common import new_id, utc_now
from app.schemas.document import Document, DocumentStatus, DocumentType
from app.services.document_parser import UnsupportedDocumentError, extract_text_from_file
from app.services.knowledge_ingestion import chunk_knowledge_document
from app.services.rfp_assessment import (
    RfpAssessmentUnavailable,
    assess_project_rfp,
    has_rfp_document,
)

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])
DbSession = Annotated[Session, Depends(get_db)]


def _ensure_project(project_id: str, db: Session) -> None:
    if not db.get(ProjectRecord, project_id):
        raise HTTPException(status_code=404, detail="Project not found")


def _save_upload(project_id: str, upload: UploadFile) -> Path:
    safe_name = Path(upload.filename or "uploaded_file").name
    project_dir = settings.upload_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    path = project_dir / safe_name
    with path.open("wb") as output:
        output.write(upload.file.read())
    return path


def _remove_existing_rfp_documents(project_id: str, db: Session) -> None:
    """Keep the MVP contract to one RFP document per project."""
    documents = db.scalars(
        select(DocumentRecord).where(
            DocumentRecord.project_id == project_id,
            DocumentRecord.document_type == DocumentType.rfp.value,
        )
    ).all()
    for document in documents:
        db.delete(document)


def _create_document(
    project_id: str,
    file: UploadFile,
    document_type: DocumentType,
    db: Session,
) -> Document:
    _ensure_project(project_id, db)
    path = _save_upload(project_id, file)

    try:
        text = extract_text_from_file(path)
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if document_type == DocumentType.rfp:
        _remove_existing_rfp_documents(project_id, db)

    document = DocumentRecord(
        id=new_id("doc"),
        project_id=project_id,
        document_type=document_type.value,
        filename=Path(file.filename or path.name).name,
        mime_type=file.content_type or "application/octet-stream",
        status=DocumentStatus.processed.value,
        created_at=utc_now(),
        stored_path=str(path),
        extracted_text=text,
    )
    db.add(document)

    if document_type == DocumentType.knowledge:
        for candidate in chunk_knowledge_document(document.id, document.filename, text):
            db.add(KnowledgeChunkRecord(**candidate.__dict__))

    db.flush()

    if document_type == DocumentType.rfp or (
        document_type == DocumentType.knowledge and has_rfp_document(project_id, db)
    ):
        try:
            assess_project_rfp(project_id, db)
        except RfpAssessmentUnavailable:
            pass

    db.commit()
    db.refresh(document)
    return document.to_schema()


@router.post(
    "/rfp",
    response_model=Document,
    status_code=status.HTTP_201_CREATED,
    operation_id="upload_rfp_document",
)
def upload_rfp_document(project_id: str, db: DbSession, file: UploadFile = File(...)) -> Document:
    """Upload and parse the RFP/tender document for a project."""
    return _create_document(project_id, file, DocumentType.rfp, db)


@router.post(
    "/knowledge",
    response_model=Document,
    status_code=status.HTTP_201_CREATED,
    operation_id="upload_knowledge_document",
)
def upload_knowledge_document(
    project_id: str,
    db: DbSession,
    file: UploadFile = File(...),
) -> Document:
    """Upload, parse, and chunk a knowledge-base document for a project."""
    return _create_document(project_id, file, DocumentType.knowledge, db)


@router.get("", response_model=list[Document], operation_id="list_documents")
def list_documents(project_id: str, db: DbSession) -> list[Document]:
    """List documents for a project."""
    _ensure_project(project_id, db)
    documents = db.scalars(
        select(DocumentRecord)
        .where(DocumentRecord.project_id == project_id)
        .order_by(DocumentRecord.created_at)
    ).all()
    return [document.to_schema() for document in documents]
