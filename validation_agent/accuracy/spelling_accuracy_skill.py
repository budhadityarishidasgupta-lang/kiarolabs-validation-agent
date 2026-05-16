from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_spelling_accuracy_skill(ctx: AuditContext) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    courses, err = safe_get_json(ctx, "/practice/spelling/courses")
    if err:
        findings.append(
            finding(
                product="SpellingSprint",
                lesson_or_paper_id="unknown",
                question_id="unknown",
                status="RISK",
                reason="Spelling course fetch failed",
                evidence=err,
                suggested_human_review_note="Check auth/access and rerun spelling prompt leakage checks.",
                severity="high",
                owner="Codex",
            )
        )
        return findings
    findings.append(
        finding(
            product="SpellingSprint",
            lesson_or_paper_id="sample",
            question_id="sample",
            status="NEEDS_REVIEW",
            reason="Automated check confirms route availability only",
            evidence=f"courses_returned={len(courses) if isinstance(courses, list) else 0}",
            suggested_human_review_note="Manually verify no pre-submit answer leakage in audio/text prompts.",
            severity="medium",
            owner="Content Review",
        )
    )
    return findings

