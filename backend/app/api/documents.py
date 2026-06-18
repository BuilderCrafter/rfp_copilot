from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import settings
from app.schemas.common import new_id, utc_now
from app.schemas.document import Document, DocumentStatus, DocumentType, KnowledgeChunk
from app.services.document_parser import UnsupportedDocumentError, extract_text_from_file
from app.services.knowledge_ingestion import chunk_knowledge_document
from app.storage.memory_store import store

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


def _ensure_project(project_id: str) -> None:
    if project_id not in store.projects:
        raise HTTPException(status_code=404, detail="Project not found")


def _save_upload(project_id: str, upload: UploadFile) -> Path:
    safe_name = Path(upload.filename or "uploaded_file").name
    project_dir = settings.upload_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    path = project_dir / safe_name
    with path.open("wb") as output:
        output.write(upload.file.read())
    return path


def _create_document(project_id: str, file: UploadFile, document_type: DocumentType) -> Document:
    _ensure_project(project_id)
    path = _save_upload(project_id, file)
    document = Document(
        id=new_id("doc"),
        project_id=project_id,
        document_type=document_type,
        filename=Path(file.filename or path.name).name,
        mime_type=file.content_type or "application/octet-stream",
        status=DocumentStatus.processing,
        created_at=utc_now(),
    )
    store.documents[document.id] = document

    try:
        text = extract_text_from_file(path)
    except UnsupportedDocumentError as exc:
        failed = document.model_copy(update={"status": DocumentStatus.failed})
        store.documents[document.id] = failed
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store.document_texts[document.id] = text

    if document_type == DocumentType.knowledge:
        for candidate in chunk_knowledge_document(document.id, document.filename, text):
            chunk = KnowledgeChunk(**candidate.__dict__)
            store.chunks[chunk.id] = chunk

    processed = document.model_copy(update={"status": DocumentStatus.processed})
    store.documents[document.id] = processed
    return processed


@router.post("/rfp", response_model=Document, status_code=status.HTTP_201_CREATED)
def upload_rfp_document(project_id: str, file: UploadFile = File(...)) -> Document:
    """Upload and parse the RFP/tender document for a project."""
    return _create_document(project_id, file, DocumentType.rfp)


@router.post("/knowledge", response_model=Document, status_code=status.HTTP_201_CREATED)
def upload_knowledge_document(project_id: str, file: UploadFile = File(...)) -> Document:
    """Upload, parse, and chunk a knowledge-base document for a project."""
    return _create_document(project_id, file, DocumentType.knowledge)


@router.get("", response_model=list[Document])
def list_documents(project_id: str) -> list[Document]:
    """List documents for a project."""
    _ensure_project(project_id)
    return [document for document in store.documents.values() if document.project_id == project_id]
