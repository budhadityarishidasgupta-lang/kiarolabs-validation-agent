from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_synonym_accuracy_skill(ctx: AuditContext) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    courses, err = safe_get_json(ctx, "/practice/words/courses")
    if err:
        findings.append(
            finding(
                product="WordSprint synonyms",
                lesson_or_paper_id="unknown",
                question_id="unknown",
                status="RISK",
                reason="Words course fetch failed",
                evidence=err,
                suggested_human_review_note="Retry with entitled student and verify synonym dataset wiring.",
                severity="high",
                owner="Codex",
            )
        )
        return findings
    synonym_lessons = []
    for course in courses if isinstance(courses, list) else []:
        cname = str(course.get("course_name", "")).lower()
        if "synonym" in cname:
            synonym_lessons.extend(course.get("lessons", []) or [])
    findings.append(
        finding(
            product="WordSprint synonyms",
            lesson_or_paper_id=str(synonym_lessons[0].get("lesson_id")) if synonym_lessons else "none",
            question_id="sample",
            status="PASS" if synonym_lessons else "NEEDS_REVIEW",
            reason="Synonym lessons discovered" if synonym_lessons else "No synonym lesson discovered in active courses payload",
            evidence=f"synonym_lessons={len(synonym_lessons)}",
            suggested_human_review_note="Review sampled headwords against approved answer metadata for unrelated/antonym drift.",
            severity="medium",
            owner="Content Review",
        )
    )
    return findings

