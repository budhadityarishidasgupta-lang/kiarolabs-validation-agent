from __future__ import annotations

import re

from validation_agent.skills.base import BaseSkill
from validation_agent.skills.checks import (
    find_regex_occurrences,
    format_hit,
    get_scan_roots,
    iter_source_files,
    looks_like_full_paid_pdf,
    safe_read_text,
)


class PrintablePreviewSkill(BaseSkill):
    skill_name = "Printable Preview"

    def run(self):
        roots = get_scan_roots()
        files = iter_source_files(roots, extensions=(".ts", ".tsx", ".js", ".jsx", ".py", ".json"))
        files_checked = [str(path) for path in roots]
        details: list[str] = []
        recommendations: list[str] = []
        status = "PASS"

        metadata_hits = find_regex_occurrences(
            files,
            [re.compile(r"\b(sampleImages|samplePdf)\b", re.IGNORECASE)],
        )
        if not metadata_hits:
            status = "RISK"
            details.append("No sampleImages/samplePdf metadata references found.")
            recommendations.append("Confirm printable metadata includes optional sampleImages/samplePdf.")
        else:
            details.extend([f"Sample metadata signal: {format_hit(*hit)}" for hit in metadata_hits[:15]])

        suspicious_pdf_hits: list[str] = []
        ambiguous_sample_hits: list[str] = []
        for path in files:
            text = safe_read_text(path)
            for match in re.findall(r"(https?://[^\s\"'`)>]+)", text):
                lower = match.lower()
                if ".pdf" not in lower:
                    continue
                if "sample" in lower or "preview" in lower:
                    if looks_like_full_paid_pdf(match):
                        suspicious_pdf_hits.append(f"{path} -> {match}")
                    continue
                if "pdf" in lower and "gumroad" not in lower:
                    ambiguous_sample_hits.append(f"{path} -> {match}")

        if suspicious_pdf_hits:
            status = "FAIL"
            details.extend([f"Potential full paid PDF sample exposure: {hit}" for hit in suspicious_pdf_hits[:20]])
            recommendations.append("Ensure samplePdf points only to controlled sample assets.")
        elif ambiguous_sample_hits and status != "FAIL":
            status = "RISK"
            details.extend([f"Ambiguous PDF asset naming: {hit}" for hit in ambiguous_sample_hits[:20]])
            recommendations.append("Use explicit sample/preview naming for public sample assets.")

        view_sample_hits = find_regex_occurrences(
            files,
            [re.compile(r"view sample", re.IGNORECASE)],
        )
        if not view_sample_hits and status == "PASS":
            status = "RISK"
            details.append("No 'View sample' action found in static scan.")

        purchase_hits = find_regex_occurrences(
            files,
            [re.compile(r"(continue with full paper|unlock full access|gumroad)", re.IGNORECASE)],
        )
        if not purchase_hits and status == "PASS":
            status = "RISK"
            details.append("No purchase CTA continuity signal found for printable flow.")

        if status == "PASS":
            status = "NEEDS_MANUAL_CHECK"
            details.append("Static checks passed. Asset protection still requires runtime/manual verification.")

        summary = "Printable preview checks complete."
        if status == "FAIL":
            summary = "Printable preview exposure failure detected."
        elif status == "RISK":
            summary = "Printable preview has risk signals requiring review."
        elif status == "NEEDS_MANUAL_CHECK":
            summary = "Printable preview static checks passed; manual verification still required."
        return self.result(
            status=status,
            summary=summary,
            details=details,
            files_checked=files_checked,
            recommendations=recommendations,
        )
