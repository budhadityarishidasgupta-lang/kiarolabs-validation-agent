from __future__ import annotations

import re

from validation_agent.skills.base import BaseSkill
from validation_agent.skills.checks import (
    detect_unlocked_query_param_trust,
    find_regex_occurrences,
    format_hit,
    get_scan_roots,
    iter_source_files,
    safe_read_text,
)


class MockSecuritySkill(BaseSkill):
    skill_name = "Mock Security"

    def run(self):
        roots = get_scan_roots()
        files = iter_source_files(roots, extensions=(".ts", ".tsx", ".js", ".jsx", ".py"))
        files_checked = [str(path) for path in roots]
        details: list[str] = []
        recommendations: list[str] = []
        status = "PASS"

        spoof_hits: list[str] = []
        for path in files:
            text = safe_read_text(path)
            if detect_unlocked_query_param_trust(text):
                spoof_hits.append(str(path))
        if spoof_hits:
            status = "FAIL"
            details.extend([f"Query-param access trust risk: {path}" for path in spoof_hits[:25]])
            recommendations.append("Do not trust unlocked=true query params for full access.")

        preview_escalation = find_regex_occurrences(
            files,
            [
                re.compile(r"mode\s*===\s*['\"]preview['\"].*(full|unlock)", re.IGNORECASE),
                re.compile(r"preview.*=>.*full", re.IGNORECASE),
            ],
        )
        if preview_escalation:
            status = "FAIL"
            details.extend([f"Preview escalation signal: {format_hit(*hit)}" for hit in preview_escalation[:20]])
            recommendations.append("Keep backend as source of truth for preview/full mock access.")

        scoring_hits = find_regex_occurrences(
            files,
            [
                re.compile(r"(preview).*(score|completed|submit)", re.IGNORECASE),
                re.compile(r"(timer).*(preview|locked)", re.IGNORECASE),
            ],
        )
        if scoring_hits and status == "PASS":
            status = "RISK"
            details.extend([f"Scoring/timer preview risk signal: {format_hit(*hit)}" for hit in scoring_hits[:20]])
            recommendations.append("Confirm preview users cannot generate full completed mock results.")

        authority_hits = find_regex_occurrences(
            files,
            [re.compile(r"(backend|server).*(access|entitl|locked)", re.IGNORECASE)],
        )
        if not authority_hits and status == "PASS":
            status = "RISK"
            details.append("No backend authority hints found for mock access in static scan.")
            recommendations.append("Manually verify backend decides preview/full mock access.")

        summary = "No mock security issues found."
        if status == "FAIL":
            summary = "Mock security failures detected."
        elif status == "RISK":
            summary = "Mock security risk signals detected; manual review required."
        return self.result(
            status=status,
            summary=summary,
            details=details,
            files_checked=files_checked,
            recommendations=recommendations,
        )
