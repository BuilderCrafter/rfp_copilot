from fastapi import APIRouter, HTTPException, status

from app.schemas.common import new_id, utc_now
from app.schemas.project import Project, ProjectCreate, ProjectStatus
from app.storage.memory_store import store

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate) -> Project:
    """Create a new RFP response project."""
    now = utc_now()
    project = Project(
        id=new_id("project"),
        name=payload.name,
        client_name=payload.client_name,
        status=ProjectStatus.active,
        created_at=now,
        updated_at=now,
    )
    store.projects[project.id] = project
    return project


@router.get("", response_model=list[Project])
def list_projects() -> list[Project]:
    """List all projects in the temporary store."""
    return list(store.projects.values())


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    """Return a project by ID."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
