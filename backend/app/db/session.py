from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.base import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create MVP tables if they do not exist.

    Alembic can replace this once the schema starts changing beyond hackathon scope.
    """
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_assessment_columns()


def _ensure_assessment_columns() -> None:
    """Keep local hackathon databases compatible after assessment schema additions."""
    inspector = inspect(engine)
    if "rfp_assessments" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("rfp_assessments")}
    if "client_submission_checklist" in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE rfp_assessments ADD COLUMN client_submission_checklist JSON")
        )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
