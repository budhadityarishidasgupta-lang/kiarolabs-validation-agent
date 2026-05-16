from __future__ import annotations

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_antonym_accuracy_skill(ctx: AuditContext) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    courses, err = safe_get_json(ctx, "/practice/words/courses")
    if err:
        findings.append(
            finding(
                product="WordSprint antonyms",
                lesson_or_paper_id="unknown",
                question_id="unknown",
                status="RISK",
                reason="Words course fetch failed",
                evidence=err,
                suggested_human_review_note="Re-run with entitled student and inspect antonym lesson data.",
                severity="high",
                owner="Codex",
            )
        )
        return findings
    antonym_lessons = []
    for course in courses if isinstance(courses, list) else []:
        cname = str(course.get("course_name", "")).lower()
        if "antonym" in cname:
            antonym_lessons.extend(course.get("lessons", []) or [])
    findings.append(
        finding(
            product="WordSprint antonyms",
            lesson_or_paper_id=str(antonym_lessons[0].get("lesson_id")) if antonym_lessons else "none",
            question_id="sample",
            status="PASS" if antonym_lessons else "NEEDS_REVIEW",
            reason="Antonym lessons discovered" if antonym_lessons else "No antonym lesson discovered in active courses payload",
            evidence=f"antonym_lessons={len(antonym_lessons)}",
            suggested_human_review_note="Validate opposite-meaning correctness against approved dataset.",
            severity="medium",
            owner="Content Review",
        )
    )
    return findings

