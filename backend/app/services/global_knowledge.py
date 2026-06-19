from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentRecord, KnowledgeChunkRecord, ProjectRecord
from app.schemas.common import new_id, utc_now
from app.schemas.document import DocumentStatus, DocumentType
from app.schemas.project import ProjectStatus
from app.services.document_parser import UnsupportedDocumentError, extract_text_from_file
from app.services.knowledge_ingestion import chunk_knowledge_document

GLOBAL_KNOWLEDGE_PROJECT_ID = "project_global_knowledge_base"
GLOBAL_KNOWLEDGE_PROJECT_NAME = "Global Knowledge Base"


def sample_knowledge_base_dir(repo_root: Path) -> Path:
    """Return the best available sample knowledge-base path for local or Docker runs."""
    local_path = repo_root / "sample_data" / "knowledge_base"
    if local_path.exists():
        return local_path
    return Path("/sample_data/knowledge_base")


def seed_global_knowledge_base(db: Session, knowledge_base_dir: Path) -> None:
    """Load bundled knowledge-base files into the shared app-wide knowledge base."""
    if not knowledge_base_dir.exists():
        return

    now = utc_now()
    project = db.get(ProjectRecord, GLOBAL_KNOWLEDGE_PROJECT_ID)
    if not project:
        project = ProjectRecord(
            id=GLOBAL_KNOWLEDGE_PROJECT_ID,
            name=GLOBAL_KNOWLEDGE_PROJECT_NAME,
            client_name=None,
            status=ProjectStatus.active.value,
            created_at=now,
            updated_at=now,
        )
        db.add(project)
        db.flush()

    existing_paths = set(
        db.scalars(
            select(DocumentRecord.stored_path).where(
                DocumentRecord.project_id == GLOBAL_KNOWLEDGE_PROJECT_ID,
                DocumentRecord.document_type == DocumentType.knowledge.value,
            )
        ).all()
    )

    for path in sorted(knowledge_base_dir.rglob("*")):
        if not path.is_file() or str(path) in existing_paths:
            continue

        try:
            text = extract_text_from_file(path)
        except UnsupportedDocumentError:
            continue

        relative_name = str(path.relative_to(knowledge_base_dir))
        document = DocumentRecord(
            id=new_id("doc"),
            project_id=GLOBAL_KNOWLEDGE_PROJECT_ID,
            document_type=DocumentType.knowledge.value,
            filename=relative_name,
            mime_type="text/markdown" if path.suffix.lower() == ".md" else "application/octet-stream",
            status=DocumentStatus.processed.value,
            created_at=now,
            stored_path=str(path),
            extracted_text=text,
        )
        db.add(document)
        db.flush()

        for candidate in chunk_knowledge_document(document.id, document.filename, text):
            db.add(KnowledgeChunkRecord(**candidate.__dict__))

    project.updated_at = utc_now()
    db.commit()
