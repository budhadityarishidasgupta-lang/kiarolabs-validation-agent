from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_entitlement_access_skill(ctx: AuditContext) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    dashboard, err = safe_get_json(ctx, "/dashboard")
    if err:
        findings.append(
            finding(
                product="Entitlement access",
                lesson_or_paper_id="dashboard",
                question_id="n/a",
                status="RISK",
                reason="Dashboard entitlement fetch failed",
                evidence=err,
                suggested_human_review_note="Confirm student credentials and entitlement API availability.",
                severity="high",
                owner="Codex",
            )
        )
        return findings
    modules = (dashboard or {}).get("modules", {}) if isinstance(dashboard, dict) else {}
    findings.append(
        finding(
            product="Entitlement access",
            lesson_or_paper_id="dashboard",
            question_id="n/a",
            status="PASS",
            reason="Dashboard module entitlement payload returned",
            evidence=f"module_keys={sorted(modules.keys()) if isinstance(modules, dict) else []}",
            suggested_human_review_note="Cross-check module unlocks against expected product purchases.",
            severity="low",
            owner="Admin",
        )
    )
    return findings

