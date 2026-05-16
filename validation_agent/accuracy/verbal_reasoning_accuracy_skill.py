from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_verbal_reasoning_accuracy_skill(ctx: AuditContext) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    papers, err = safe_get_json(ctx, "/practice/vr/papers")
    if err:
        findings.append(
            finding(
                product="Verbal Reasoning",
                lesson_or_paper_id="unknown",
                question_id="unknown",
                status="RISK",
                reason="VR paper list fetch failed",
                evidence=err,
                suggested_human_review_note="Verify VR entitlement/paper readiness and rerun answer-key alignment checks.",
                severity="high",
                owner="Codex",
            )
        )
        return findings
    count = len(papers) if isinstance(papers, list) else 0
    first_code = str(papers[0].get("paper_code")) if count else "none"
    findings.append(
        finding(
            product="Verbal Reasoning",
            lesson_or_paper_id=first_code,
            question_id="sample",
            status="PASS" if count else "NEEDS_REVIEW",
            reason="VR papers available for audit" if count else "No VR papers returned for audit",
            evidence=f"papers_count={count}",
            suggested_human_review_note="Cross-check visible answers against approved VR answer key rows.",
            severity="medium",
            owner="Content Review",
        )
    )
    return findings

