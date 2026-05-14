from __future__ import annotations

import re

from validation_agent.skills.base import BaseSkill
from validation_agent.skills.checks import (
    find_regex_occurrences,
    format_hit,
    get_scan_roots,
    iter_source_files,
    safe_read_text,
)


class ArchitectureGuardrailSkill(BaseSkill):
    skill_name = "Architecture Guardrails"

    def run(self):
        roots = get_scan_roots()
        files = iter_source_files(roots)
        details: list[str] = []
        files_checked = [str(path) for path in roots]
        recommendations: list[str] = []
        status = "PASS"

        frontend_files = [path for path in files if "/src/" in str(path).replace("\\", "/")]
        sql_hits = find_regex_occurrences(
            frontend_files,
            [
                re.compile(
                    r"\bSELECT\s+[\w\*,\s]+\s+FROM\s+[a-z_][a-z0-9_]*\s+(WHERE|JOIN|ORDER|GROUP|LIMIT)\b",
                    re.IGNORECASE,
                ),
                re.compile(r"\bINSERT\s+INTO\b", re.IGNORECASE),
                re.compile(r"\bUPDATE\s+\w+\s+SET\b", re.IGNORECASE),
                re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
            ],
        )
        if sql_hits:
            status = "FAIL"
            details.extend([f"SQL in frontend: {format_hit(*hit)}" for hit in sql_hits[:20]])
            recommendations.append("Move SQL/database access into backend repository layer.")

        cross_app_hits = []
        for path in files:
            text = safe_read_text(path)
            for index, line in enumerate(text.splitlines(), start=1):
                lower = line.lower()
                app_prefixes = ["math_", "spelling_", "words_", "comprehension_"]
                hits = sum(1 for prefix in app_prefixes if prefix in lower)
                if hits >= 2:
                    cross_app_hits.append((path, index, line.strip()))
                    continue
                if "cross-app" in lower or "cross app" in lower:
                    cross_app_hits.append((path, index, line.strip()))
        if cross_app_hits:
            status = "FAIL"
            details.extend([f"Cross-app access signal: {format_hit(*hit)}" for hit in cross_app_hits[:20]])
            recommendations.append("Keep each app's data model isolated and avoid cross-app joins.")

        db_create_hits = find_regex_occurrences(
            files,
            [
                re.compile(r"CREATE\s+DATABASE", re.IGNORECASE),
                re.compile(r"sqlite://", re.IGNORECASE),
            ],
        )
        if db_create_hits:
            status = "FAIL"
            details.extend([f"New DB creation signal: {format_hit(*hit)}" for hit in db_create_hits[:20]])
            recommendations.append("Use the existing shared Postgres DB and avoid creating new databases.")

        frontend_authority_hits = find_regex_occurrences(
            frontend_files,
            [
                re.compile(r"(isPaid|fullAccess|entitled)\s*=\s*true", re.IGNORECASE),
                re.compile(r"localStorage.*(paid|entitled|unlocked)", re.IGNORECASE),
            ],
        )
        if frontend_authority_hits and status != "FAIL":
            status = "RISK"
            details.extend(
                [f"Frontend access authority risk: {format_hit(*hit)}" for hit in frontend_authority_hits[:20]]
            )
            recommendations.append("Ensure backend remains source of truth for paid/preview access.")

        metadata_hits = find_regex_occurrences(
            files,
            [
                re.compile(r'"(pdf_url|file_url|download_url)"\s*:\s*"https?://', re.IGNORECASE),
                re.compile(r"public.*(pdf|asset).*paid", re.IGNORECASE),
            ],
        )
        if metadata_hits and status == "PASS":
            status = "RISK"
            details.extend([f"Public metadata exposure risk: {format_hit(*hit)}" for hit in metadata_hits[:20]])
            recommendations.append("Verify public metadata does not include paid-content direct URLs.")

        summary = "No architecture guardrail violations found."
        if status == "FAIL":
            summary = "Architecture guardrail violations detected."
        elif status == "RISK":
            summary = "Architecture guardrail risks detected; manual review advised."
        return self.result(
            status=status,
            summary=summary,
            details=details,
            files_checked=files_checked,
            recommendations=recommendations,
        )
