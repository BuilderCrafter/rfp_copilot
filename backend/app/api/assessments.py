from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ProjectRecord, RfpAssessmentRecord
from app.schemas.assessment import RfpAssessment
from app.schemas.common import ErrorResponse
from app.services.rfp_assessment import RfpAssessmentUnavailable, assess_project_rfp

router = APIRouter(prefix="/projects/{project_id}", tags=["assessments"])
DbSession = Annotated[Session, Depends(get_db)]


def _ensure_project(project_id: str, db: Session) -> None:
    if not db.get(ProjectRecord, project_id):
        raise HTTPException(status_code=404, detail="Project not found")


@router.get(
    "/rfp_assessment",
    response_model=RfpAssessment,
    responses={404: {"model": ErrorResponse}},
    operation_id="get_rfp_assessment",
)
def get_rfp_assessment(project_id: str, db: DbSession) -> RfpAssessment:
    """Return the latest stored RFP bid/no-bid and completeness assessment."""
    _ensure_project(project_id, db)
    assessment = db.scalars(
        select(RfpAssessmentRecord).where(RfpAssessmentRecord.project_id == project_id)
    ).first()
    if assessment:
        return assessment.to_schema()

    try:
        result = assess_project_rfp(project_id, db)
    except RfpAssessmentUnavailable as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    return result


@router.post(
    "/assess_rfp",
    response_model=RfpAssessment,
    responses={404: {"model": ErrorResponse}},
    operation_id="assess_rfp",
)
def assess_rfp(project_id: str, db: DbSession) -> RfpAssessment:
    """Re-run the RFP bid/no-bid and missing-information assessment."""
    _ensure_project(project_id, db)
    try:
        result = assess_project_rfp(project_id, db)
    except RfpAssessmentUnavailable as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    return result
