from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.project import Project, ProjectStatus

if TYPE_CHECKING:
    from app.models.document import DocumentRecord
    from app.models.question import RfpQuestionRecord


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    documents: Mapped[list["DocumentRecord"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    questions: Mapped[list["RfpQuestionRecord"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def to_schema(self) -> Project:
        return Project(
            id=self.id,
            name=self.name,
            client_name=self.client_name,
            status=ProjectStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
