from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ProjectStatus(StrEnum):
    active = "active"
    completed = "completed"
    archived = "archived"


class ProjectCreate(BaseModel):
    name: str
    client_name: str | None = None


class Project(BaseModel):
    id: str
    name: str
    client_name: str | None = None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
