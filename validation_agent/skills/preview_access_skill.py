from __future__ import annotations

import re

from validation_agent.skills.base import BaseSkill
from validation_agent.skills.checks import (
    find_regex_occurrences,
    format_hit,
    get_scan_roots,
    iter_source_files,
    load_simple_yaml,
    repo_root,
)


class PreviewAccessSkill(BaseSkill):
    skill_name = "Preview Access"

    def run(self):
        roots = get_scan_roots()
        files = iter_source_files(roots)
        files_checked = [str(path) for path in roots]
        details: list[str] = []
        recommendations: list[str] = []
        status = "PASS"

        config_path = repo_root() / "validation_agent" / "skill_config" / "preview_contract.yml"
        contract = load_simple_yaml(config_path)
        files_checked.append(str(config_path))

        if contract.get("preview_question_limit") != 5:
            status = "FAIL"
            details.append(
                f"preview_question_limit expected 5, found {contract.get('preview_question_limit')} in {config_path}."
            )
            recommendations.append("Set preview_question_limit to 5 in preview_contract.yml.")

        access_states = set(contract.get("access_states", []))
        expected_states = {"full", "preview", "locked"}
        if access_states != expected_states:
            status = "FAIL"
            details.append(f"access_states expected {sorted(expected_states)}, found {sorted(access_states)}.")
            recommendations.append("Ensure access_states includes exactly full, preview, locked.")

        authority_hits = find_regex_occurrences(
            files,
            [
                re.compile(r"(preview|locked|full).*(access|entitl|authorit)", re.IGNORECASE),
                re.compile(r"question_limit.*5", re.IGNORECASE),
            ],
        )
        if not authority_hits and status != "FAIL":
            status = "RISK"
            details.append("Could not statically confirm backend authority for preview/full/locked handling.")
            recommendations.append("Verify backend endpoints enforce preview lock state at question 6.")
        else:
            details.extend([f"Preview authority signal: {format_hit(*hit)}" for hit in authority_hits[:20]])

        q6_hits = find_regex_occurrences(
            files,
            [
                re.compile(r"(question\s*6|q6).*(locked|preview)", re.IGNORECASE),
                re.compile(r"preview_question_limit", re.IGNORECASE),
            ],
        )
        if not q6_hits and status == "PASS":
            status = "RISK"
            details.append("No static Q6 lock signals found for Online Practice/Maths Mock.")
            recommendations.append("Add regression tests or explicit guard comments for Q6 lock behavior.")

        paid_routing_hits = find_regex_occurrences(
            files,
            [re.compile(r"(paid|full).*(locked|preview)", re.IGNORECASE)],
        )
        if paid_routing_hits and status == "PASS":
            status = "RISK"
            details.extend([f"Paid routing risk signal: {format_hit(*hit)}" for hit in paid_routing_hits[:10]])

        details.append("Dynamic API checks for Q1-Q5 pass/Q6 lock were not executed in static scan mode.")
        if status == "PASS":
            status = "NEEDS_MANUAL_CHECK"
        elif status == "RISK":
            details.append("Manual API verification required for preview contract behavior.")

        summary = "Preview contract statically validated; dynamic API checks still required."
        if status == "FAIL":
            summary = "Preview contract violations detected."
        return self.result(
            status=status,
            summary=summary,
            details=details,
            files_checked=files_checked,
            recommendations=recommendations,
        )
