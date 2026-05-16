from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.types import AccuracyFinding


def safe_get_json(ctx: AuditContext, path: str, role: str = "student"):
    if not ctx.client:
        return None, "client_unavailable"
    token = None
    if role == "student":
        token = ctx.student_login.token if ctx.student_login else None
    elif role == "admin":
        token = ctx.admin_login.token if ctx.admin_login else None
    if not token:
        return None, f"{role}_login_unavailable"
    try:
        return ctx.client.request_json("GET", path, token=token), ""
    except Exception as exc:  # pragma: no cover - runtime network variability
        return None, str(exc)


def finding(
    *,
    product: str,
    lesson_or_paper_id: str,
    question_id: str,
    status: str,
    reason: str,
    evidence: str,
    suggested_human_review_note: str,
    severity: str = "medium",
    owner: str = "Content Review",
) -> AccuracyFinding:
    return AccuracyFinding(
        product=product,
        lesson_or_paper_id=lesson_or_paper_id,
        question_id=question_id,
        status=status,  # type: ignore[arg-type]
        reason=reason,
        evidence=evidence,
        suggested_human_review_note=suggested_human_review_note,
        severity=severity,  # type: ignore[arg-type]
        recommended_owner=owner,  # type: ignore[arg-type]
    )

