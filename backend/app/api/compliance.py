from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ProjectRecord, RfpComplianceReportRecord
from app.schemas.common import ErrorResponse
from app.schemas.compliance import RfpComplianceReport
from app.services.compliance_check import run_project_compliance_check

router = APIRouter(prefix="/projects/{project_id}", tags=["compliance"])
DbSession = Annotated[Session, Depends(get_db)]


def _ensure_project(project_id: str, db: Session) -> None:
    if not db.get(ProjectRecord, project_id):
        raise HTTPException(status_code=404, detail="Project not found")


@router.get(
    "/compliance_check",
    response_model=RfpComplianceReport,
    responses={404: {"model": ErrorResponse}},
    operation_id="get_compliance_check",
)
def get_compliance_check(project_id: str, db: DbSession) -> RfpComplianceReport:
    """Return the latest stored compliance report, or generate one if missing."""
    _ensure_project(project_id, db)
    report = db.scalars(
        select(RfpComplianceReportRecord).where(
            RfpComplianceReportRecord.project_id == project_id
        )
    ).first()
    if report:
        return report.to_schema()

    result = run_project_compliance_check(project_id, db)
    db.commit()
    return result


@router.post(
    "/compliance_check",
    response_model=RfpComplianceReport,
    responses={404: {"model": ErrorResponse}},
    operation_id="run_compliance_check",
)
def run_compliance_check(project_id: str, db: DbSession) -> RfpComplianceReport:
    """Re-run the submission readiness compliance check for a project."""
    _ensure_project(project_id, db)
    result = run_project_compliance_check(project_id, db)
    db.commit()
    return result
