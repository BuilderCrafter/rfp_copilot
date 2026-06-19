from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.document import Document, DocumentStatus, DocumentType, KnowledgeChunk

if TYPE_CHECKING:
    from app.models.project import ProjectRecord


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stored_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["ProjectRecord"] = relationship(back_populates="documents")
    chunks: Mapped[list["KnowledgeChunkRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def to_schema(self) -> Document:
        return Document(
            id=self.id,
            project_id=self.project_id,
            document_type=DocumentType(self.document_type),
            filename=self.filename,
            mime_type=self.mime_type,
            status=DocumentStatus(self.status),
            created_at=self.created_at,
        )


class KnowledgeChunkRecord(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True, nullable=False)
    document_title: Mapped[str] = mapped_column(String(512), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    document: Mapped[DocumentRecord] = relationship(back_populates="chunks")

    def to_schema(self) -> KnowledgeChunk:
        return KnowledgeChunk(
            id=self.id,
            document_id=self.document_id,
            document_title=self.document_title,
            text=self.text,
            page_number=self.page_number,
            section_title=self.section_title,
            chunk_index=self.chunk_index,
        )
