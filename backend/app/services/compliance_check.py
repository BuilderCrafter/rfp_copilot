from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AnswerRecord,
    CitationRecord,
    DocumentRecord,
    RfpAssessmentRecord,
    RfpComplianceReportRecord,
    RfpQuestionRecord,
)
from app.schemas.answer import AnswerStatus
from app.schemas.assessment import (
    BidRecommendation,
    RequirementSeverity,
    SubmissionRequirementStatus,
)
from app.schemas.common import new_id, utc_now
from app.schemas.compliance import (
    ComplianceIssue,
    ComplianceIssueCategory,
    ComplianceIssueSeverity,
    ComplianceReportStatus,
    ComplianceSummary,
    RfpComplianceReport,
)
from app.schemas.document import DocumentType


def _severity(value: RequirementSeverity) -> ComplianceIssueSeverity:
    return ComplianceIssueSeverity(value.value)


def _issue(
    category: ComplianceIssueCategory,
    severity: ComplianceIssueSeverity,
    message: str,
    recommended_action: str,
    requirement_id: str | None = None,
    answer_id: str | None = None,
    assessment_item_id: str | None = None,
    source: str | None = None,
) -> ComplianceIssue:
    return ComplianceIssue(
        id=new_id("issue"),
        category=category,
        severity=severity,
        message=message,
        recommended_action=recommended_action,
        requirement_id=requirement_id,
        answer_id=answer_id,
        assessment_item_id=assessment_item_id,
        source=source,
    )


def _latest_assessment(project_id: str, db: Session) -> RfpAssessmentRecord | None:
    return db.scalars(
        select(RfpAssessmentRecord).where(RfpAssessmentRecord.project_id == project_id)
    ).first()


def _has_rfp_document(project_id: str, db: Session) -> bool:
    return (
        db.scalars(
            select(DocumentRecord)
            .where(
                DocumentRecord.project_id == project_id,
                DocumentRecord.document_type == DocumentType.rfp.value,
            )
            .order_by(DocumentRecord.created_at.desc())
        ).first()
        is not None
    )


def _summary_text(status: ComplianceReportStatus, issues: list[ComplianceIssue]) -> str:
    counts = Counter(issue.severity.value for issue in issues)
    blocker_count = counts[ComplianceIssueSeverity.critical.value] + counts[
        ComplianceIssueSeverity.high.value
    ]
    warning_count = counts[ComplianceIssueSeverity.medium.value] + counts[
        ComplianceIssueSeverity.low.value
    ]

    if status == ComplianceReportStatus.passed:
        return "Compliance check passed. All extracted requirements have reviewed answers and no blocking checklist issues were found."
    if status == ComplianceReportStatus.blocked:
        return (
            f"Submission is blocked by {blocker_count} issue(s). "
            f"{warning_count} additional warning(s) should also be reviewed."
        )
    return f"Compliance check has {warning_count} warning(s), but no blocking issues."


def _report_status(issues: list[ComplianceIssue]) -> ComplianceReportStatus:
    severities = {issue.severity for issue in issues}
    if ComplianceIssueSeverity.critical in severities or ComplianceIssueSeverity.high in severities:
        return ComplianceReportStatus.blocked
    if issues:
        return ComplianceReportStatus.warnings
    return ComplianceReportStatus.passed


def run_project_compliance_check(project_id: str, db: Session) -> RfpComplianceReport:
    """Evaluate whether a project is ready for final RFP submission."""
    questions = db.scalars(
        select(RfpQuestionRecord)
        .where(RfpQuestionRecord.project_id == project_id)
        .order_by(RfpQuestionRecord.order_index)
    ).all()
    answers = db.scalars(
        select(AnswerRecord).where(
            AnswerRecord.question_id.in_([question.id for question in questions])
        )
    ).all()
    answers_by_question_id = {answer.question_id: answer for answer in answers}
    citations = db.scalars(
        select(CitationRecord).where(CitationRecord.answer_id.in_([answer.id for answer in answers]))
    ).all()
    citation_count_by_answer_id = Counter(citation.answer_id for citation in citations)

    issues: list[ComplianceIssue] = []

    if not _has_rfp_document(project_id, db):
        issues.append(
            _issue(
                category=ComplianceIssueCategory.rfp_missing,
                severity=ComplianceIssueSeverity.critical,
                message="No RFP document has been uploaded for this project.",
                recommended_action="Upload and process the RFP before compliance review.",
                source="documents",
            )
        )

    if not questions:
        issues.append(
            _issue(
                category=ComplianceIssueCategory.requirements_not_extracted,
                severity=ComplianceIssueSeverity.critical,
                message="No RFP requirements have been extracted for this project.",
                recommended_action="Run requirement extraction before compliance review.",
                source="requirements",
            )
        )

    for question in questions:
        answer = answers_by_question_id.get(question.id)
        if not answer:
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.unanswered_requirement,
                    severity=ComplianceIssueSeverity.critical,
                    message=f"Requirement is missing an answer: {question.question_text}",
                    recommended_action="Draft, review, and approve an answer for this requirement.",
                    requirement_id=question.id,
                    source="answers",
                )
            )
            continue

        answer_status = AnswerStatus(answer.status)
        if answer_status == AnswerStatus.drafted:
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.unapproved_answer,
                    severity=ComplianceIssueSeverity.high,
                    message=f"Requirement has a draft answer that is not reviewed: {question.question_text}",
                    recommended_action="Review the draft answer and mark it approved or edited before submission.",
                    requirement_id=question.id,
                    answer_id=answer.id,
                    source="answers",
                )
            )
        elif answer_status == AnswerStatus.flagged:
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.flagged_answer,
                    severity=ComplianceIssueSeverity.critical,
                    message=f"Requirement answer is flagged for review: {question.question_text}",
                    recommended_action="Resolve the review flag before submission.",
                    requirement_id=question.id,
                    answer_id=answer.id,
                    source="answers",
                )
            )
        elif answer_status == AnswerStatus.rejected:
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.rejected_answer,
                    severity=ComplianceIssueSeverity.critical,
                    message=f"Requirement answer was rejected: {question.question_text}",
                    recommended_action="Replace the rejected answer or explicitly remove the requirement from scope.",
                    requirement_id=question.id,
                    answer_id=answer.id,
                    source="answers",
                )
            )

        if (
            answer_status in {AnswerStatus.approved, AnswerStatus.edited}
            and citation_count_by_answer_id[answer.id] == 0
            and not answer.review_note
        ):
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.uncited_answer,
                    severity=ComplianceIssueSeverity.medium,
                    message=f"Reviewed answer has no citations or reviewer note: {question.question_text}",
                    recommended_action="Add a reviewer note explaining source basis, or regenerate with citations.",
                    requirement_id=question.id,
                    answer_id=answer.id,
                    source="citations",
                )
            )

    assessment_record = _latest_assessment(project_id, db)
    if not assessment_record:
        issues.append(
            _issue(
                category=ComplianceIssueCategory.assessment_missing,
                severity=ComplianceIssueSeverity.high,
                message="No RFP assessment is stored for this project.",
                recommended_action="Run the RFP assessment before submission readiness review.",
                source="assessment",
            )
        )
    else:
        assessment = assessment_record.to_schema()
        if assessment.recommendation == BidRecommendation.no_bid:
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.no_bid_recommendation,
                    severity=ComplianceIssueSeverity.critical,
                    message="The latest RFP assessment recommends no-bid.",
                    recommended_action="Resolve or override the no-bid recommendation before submission.",
                    source="assessment",
                )
            )
        elif assessment.recommendation == BidRecommendation.needs_review:
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.assessment_needs_review,
                    severity=ComplianceIssueSeverity.high,
                    message="The latest RFP assessment requires bid-manager review.",
                    recommended_action="Review assessment risks and record a bid/no-bid decision before submission.",
                    source="assessment",
                )
            )

        for item in assessment.missing_information:
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.missing_rfp_information,
                    severity=_severity(item.severity),
                    message=f"RFP information is {item.status.value}: {item.label}",
                    recommended_action=item.requested_action,
                    assessment_item_id=item.requirement_id,
                    source="assessment.missing_information",
                )
            )

        for item in assessment.client_submission_checklist:
            if item.status == SubmissionRequirementStatus.optional:
                continue
            severity = (
                ComplianceIssueSeverity.medium
                if item.status == SubmissionRequirementStatus.conditional
                else _severity(item.severity)
            )
            issues.append(
                _issue(
                    category=ComplianceIssueCategory.submission_item_open,
                    severity=severity,
                    message=f"Submission package item needs tracking: {item.label}",
                    recommended_action=item.requested_action,
                    assessment_item_id=item.id,
                    source="assessment.client_submission_checklist",
                )
            )

    approved_or_edited = sum(
        1
        for answer in answers
        if AnswerStatus(answer.status) in {AnswerStatus.approved, AnswerStatus.edited}
    )
    summary = ComplianceSummary(
        total_requirements=len(questions),
        answered_requirements=len(answers_by_question_id),
        approved_or_edited_answers=approved_or_edited,
        drafted_answers=sum(1 for answer in answers if AnswerStatus(answer.status) == AnswerStatus.drafted),
        flagged_answers=sum(1 for answer in answers if AnswerStatus(answer.status) == AnswerStatus.flagged),
        rejected_answers=sum(1 for answer in answers if AnswerStatus(answer.status) == AnswerStatus.rejected),
        missing_answers=max(0, len(questions) - len(answers_by_question_id)),
        issues_by_severity=dict(Counter(issue.severity.value for issue in issues)),
    )
    status = _report_status(issues)
    now = utc_now()

    payload = {
        "status": status.value,
        "summary_text": _summary_text(status, issues),
        "summary": summary.model_dump(mode="json"),
        "issues": [issue.model_dump(mode="json") for issue in issues],
        "updated_at": now,
    }
    existing = db.scalars(
        select(RfpComplianceReportRecord).where(
            RfpComplianceReportRecord.project_id == project_id
        )
    ).first()

    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        report = existing
    else:
        report = RfpComplianceReportRecord(
            id=new_id("compliance"),
            project_id=project_id,
            generated_at=now,
            **payload,
        )
        db.add(report)

    db.flush()
    return report.to_schema()
