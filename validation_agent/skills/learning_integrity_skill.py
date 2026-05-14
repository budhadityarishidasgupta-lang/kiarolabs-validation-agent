from __future__ import annotations

import re

from validation_agent.skills.base import BaseSkill
from validation_agent.skills.checks import (
    find_regex_occurrences,
    format_hit,
    get_scan_roots,
    iter_source_files,
)


class LearningIntegritySkill(BaseSkill):
    skill_name = "Learning Integrity"

    def run(self):
        roots = get_scan_roots()
        files = iter_source_files(roots)
        files_checked = [str(path) for path in roots]
        details: list[str] = []
        recommendations: list[str] = []
        status = "PASS"

        leak_patterns = [
            re.compile(r"['\"](correct_answer|answer_key|expected_answer)['\"]\s*:", re.IGNORECASE),
            re.compile(r"\b(question|metadata)\b.*\b(correct_answer|answer_key|expected_answer)\b", re.IGNORECASE),
        ]
        leak_hits = []
        for hit in find_regex_occurrences(files, leak_patterns):
            path, _, _ = hit
            normalized = str(path).lower().replace("\\", "/")
            if (
                "/tests/" in normalized
                or "/fixtures/" in normalized
                or "/app/admin/" in normalized
                or "/database_init" in normalized
                or "/migration" in normalized
            ):
                continue
            if "/app/practice/" not in normalized and "/growth-leap-studio/src/pages/practice" not in normalized:
                continue
            leak_hits.append(hit)
        if leak_hits:
            status = "RISK"
            details.extend([f"Potential answer leak: {format_hit(*hit)}" for hit in leak_hits[:25]])
            recommendations.append("Verify these fields are never present in pre-submit question payloads.")

            frontend_exposure = [
                hit
                for hit in leak_hits
                if "/growth-leap-studio/src/" in str(hit[0]).replace("\\", "/").lower()
            ]
            if frontend_exposure:
                status = "FAIL"
                recommendations.append("Remove answer key fields from frontend pre-submit state immediately.")

        lesson_scope_hits = find_regex_occurrences(
            files,
            [re.compile(r"/practice/session/next(?!.*lesson_id)", re.IGNORECASE)],
        )
        if lesson_scope_hits and status not in {"FAIL", "RISK"}:
            status = "RISK"
            details.extend([f"Lesson scope risk: {format_hit(*hit)}" for hit in lesson_scope_hits[:20]])
            recommendations.append("Pass lesson-scoped IDs where lesson-aware sequencing is required.")

        overwrite_hits = find_regex_occurrences(
            files,
            [
                re.compile(r"\b(UPDATE|DELETE)\b.*\battempt", re.IGNORECASE),
                re.compile(r"\boverwrite\b.*\bhistory", re.IGNORECASE),
            ],
        )
        if overwrite_hits:
            status = "FAIL"
            details.extend([f"Attempt overwrite pattern: {format_hit(*hit)}" for hit in overwrite_hits[:20]])
            recommendations.append("Keep attempts append-only and derive adaptivity from attempt history.")

        summary = "No learning integrity issues found."
        if status == "FAIL":
            summary = "Learning integrity failures detected."
        elif status == "RISK":
            summary = "Learning integrity risks detected; manual follow-up recommended."
        return self.result(
            status=status,
            summary=summary,
            details=details,
            files_checked=files_checked,
            recommendations=recommendations,
        )
