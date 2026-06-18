from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class DocumentType(StrEnum):
    rfp = "rfp"
    knowledge = "knowledge"


class DocumentStatus(StrEnum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class Document(BaseModel):
    id: str
    project_id: str
    document_type: DocumentType
    filename: str
    mime_type: str
    status: DocumentStatus
    created_at: datetime


class KnowledgeChunk(BaseModel):
    id: str
    document_id: str
    document_title: str
    text: str
    page_number: int | None = None
    section_title: str | None = None
    chunk_index: int
