from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    detail: str


def new_id(prefix: str) -> str:
    """Create readable demo IDs while keeping a prefix that identifies the entity type."""
    return f"{prefix}_{uuid4().hex[:12]}"


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)
