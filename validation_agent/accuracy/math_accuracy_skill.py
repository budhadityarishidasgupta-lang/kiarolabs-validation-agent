from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_math_accuracy_skill(ctx: AuditContext) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    lessons, err = safe_get_json(ctx, "/practice/math/lessons")
    if err:
        findings.append(
            finding(
                product="MathSprint",
                lesson_or_paper_id="unknown",
                question_id="unknown",
                status="RISK",
                reason="Math lesson fetch failed",
                evidence=err,
                suggested_human_review_note="Verify student entitlement and API availability before content audit.",
                severity="high",
                owner="Codex",
            )
        )
        return findings
    findings.append(
        finding(
            product="MathSprint",
            lesson_or_paper_id=str((lessons or [{}])[0].get("lesson_id", "n/a")) if isinstance(lessons, list) else "n/a",
            question_id="sample",
            status="PASS",
            reason="Math endpoint reachable for lesson sampling",
            evidence=f"lessons_count={len(lessons) if isinstance(lessons, list) else 0}",
            suggested_human_review_note="Run deeper per-question calculation checks against approved answer sources.",
            severity="low",
            owner="Content Review",
        )
    )
    return findings

