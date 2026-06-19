from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ProjectRecord
from app.schemas.common import ErrorResponse, new_id, utc_now
from app.schemas.project import Project, ProjectCreate, ProjectStatus
from app.services.global_knowledge import GLOBAL_KNOWLEDGE_PROJECT_ID

router = APIRouter(prefix="/projects", tags=["projects"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_project",
)
def create_project(payload: ProjectCreate, db: DbSession) -> Project:
    """Create a new RFP response project."""
    now = utc_now()
    project = ProjectRecord(
        id=new_id("project"),
        name=payload.name,
        client_name=payload.client_name,
        status=ProjectStatus.active.value,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project.to_schema()


@router.get("", response_model=list[Project], operation_id="list_projects")
def list_projects(db: DbSession) -> list[Project]:
    """List all persisted projects."""
    projects = db.scalars(
        select(ProjectRecord)
        .where(ProjectRecord.id != GLOBAL_KNOWLEDGE_PROJECT_ID)
        .order_by(ProjectRecord.created_at.desc())
    ).all()
    return [project.to_schema() for project in projects]


@router.get(
    "/{project_id}",
    response_model=Project,
    responses={404: {"model": ErrorResponse}},
    operation_id="get_project",
)
def get_project(project_id: str, db: DbSession) -> Project:
    """Return a project by ID."""
    project = db.get(ProjectRecord, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_schema()
