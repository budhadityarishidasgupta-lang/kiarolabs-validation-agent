from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_compound_word_accuracy_skill(ctx: AuditContext) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    courses, err = safe_get_json(ctx, "/practice/words/courses")
    if err:
        findings.append(
            finding(
                product="Compound words",
                lesson_or_paper_id="unknown",
                question_id="unknown",
                status="RISK",
                reason="Words course fetch failed",
                evidence=err,
                suggested_human_review_note="Retry with entitled student and inspect compound-word lessons.",
                severity="high",
                owner="Codex",
            )
        )
        return findings
    compound_lessons = []
    for course in courses if isinstance(courses, list) else []:
        cname = str(course.get("course_name", "")).lower()
        if "compound" in cname:
            compound_lessons.extend(course.get("lessons", []) or [])
    findings.append(
        finding(
            product="Compound words",
            lesson_or_paper_id=str(compound_lessons[0].get("lesson_id")) if compound_lessons else "none",
            question_id="sample",
            status="PASS" if compound_lessons else "NEEDS_REVIEW",
            reason="Compound-word lessons discovered" if compound_lessons else "No compound-word lessons discovered in active courses payload",
            evidence=f"compound_lessons={len(compound_lessons)}",
            suggested_human_review_note="Validate expected compounds against approved answer list and flag non-word combinations.",
            severity="medium",
            owner="Content Review",
        )
    )
    return findings

