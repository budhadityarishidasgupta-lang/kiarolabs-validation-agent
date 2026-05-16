from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_admin_flow_skill(ctx: AuditContext) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    users, users_err = safe_get_json(ctx, "/admin/users", role="admin")
    purchases, purchases_err = safe_get_json(ctx, "/admin/purchases/events", role="admin")
    if users_err:
        findings.append(
            finding(
                product="Admin flow",
                lesson_or_paper_id="users",
                question_id="n/a",
                status="FAIL",
                reason="Admin users endpoint unavailable",
                evidence=users_err,
                suggested_human_review_note="Confirm admin auth and backend admin route protection/availability.",
                severity="critical",
                owner="Codex",
            )
        )
    else:
        findings.append(
            finding(
                product="Admin flow",
                lesson_or_paper_id="users",
                question_id="n/a",
                status="PASS",
                reason="Admin users endpoint reachable",
                evidence=f"user_count={len(users) if isinstance(users, list) else 'n/a'}",
                suggested_human_review_note="Use admin panel to verify support workflows and access controls.",
                severity="low",
                owner="Admin",
            )
        )
    if purchases_err:
        findings.append(
            finding(
                product="Admin flow",
                lesson_or_paper_id="purchase_tracking",
                question_id="n/a",
                status="RISK",
                reason="Admin purchase reporting endpoint unavailable",
                evidence=purchases_err,
                suggested_human_review_note="Verify purchase-report route and admin role gating.",
                severity="high",
                owner="Codex",
            )
        )
    else:
        count = purchases.get("count") if isinstance(purchases, dict) else "n/a"
        findings.append(
            finding(
                product="Admin flow",
                lesson_or_paper_id="purchase_tracking",
                question_id="n/a",
                status="PASS",
                reason="Admin purchase reporting endpoint reachable",
                evidence=f"purchase_event_count={count}",
                suggested_human_review_note="Inspect failed/unknown product events for support traceability.",
                severity="low",
                owner="Admin",
            )
        )
    return findings

