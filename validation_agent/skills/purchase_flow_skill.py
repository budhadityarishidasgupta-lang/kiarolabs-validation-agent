from __future__ import annotations

import re

from validation_agent.skills.base import BaseSkill
from validation_agent.skills.checks import (
    extract_urls,
    find_regex_occurrences,
    format_hit,
    get_scan_roots,
    iter_source_files,
    load_json,
    repo_root,
    safe_read_text,
)


class PurchaseFlowSkill(BaseSkill):
    skill_name = "Purchase Flow"

    def run(self):
        roots = get_scan_roots()
        files = iter_source_files(roots, extensions=(".ts", ".tsx", ".js", ".jsx", ".py", ".json"))
        files_checked = [str(path) for path in roots]
        details: list[str] = []
        recommendations: list[str] = []
        status = "PASS"

        baseline_path = repo_root() / "validation_agent" / "skill_config" / "purchase_link_baseline.json"
        baseline = load_json(baseline_path)
        files_checked.append(str(baseline_path))

        baseline_urls = set(baseline.get("purchase_urls", []))
        collected_urls: set[str] = set()
        for path in files:
            text = safe_read_text(path)
            if "gumroad" not in text.lower() and "purchase" not in text.lower():
                continue
            for url in extract_urls(text):
                if "gumroad.com" in url.lower() or "purchase" in url.lower():
                    collected_urls.add(url)

        if not baseline_urls or baseline.get("status") == "NEEDS_MANUAL_CHECK":
            status = "NEEDS_MANUAL_CHECK"
            details.append(
                "Purchase baseline is missing or not approved. Run `python -m validation_agent.skills.purchase_baseline`."
            )
            recommendations.append("Approve and commit the first purchase URL baseline.")
        else:
            missing = sorted(url for url in baseline_urls if url not in collected_urls)
            unexpected = sorted(url for url in collected_urls if url not in baseline_urls)
            if missing or unexpected:
                status = "FAIL"
                if missing:
                    details.append(f"Baseline purchase URLs missing in current code: {missing}")
                if unexpected:
                    details.append(f"New purchase URLs not in baseline: {unexpected}")
                recommendations.append("Review purchase URL drift and update baseline only after approval.")

        intent_hits = find_regex_occurrences(
            files,
            [
                re.compile(r"purchase[_-]?intent", re.IGNORECASE),
                re.compile(r"post[_-]?login.*purchase", re.IGNORECASE),
            ],
        )
        if not intent_hits and status == "PASS":
            status = "RISK"
            details.append("Could not find purchase intent storage/resume signals.")
            recommendations.append("Verify post-login purchase intent resume behavior is still wired.")
        else:
            details.extend([f"Purchase intent signal: {format_hit(*hit)}" for hit in intent_hits[:10]])

        redirect_hits = find_regex_occurrences(
            files,
            [re.compile(r"(redirect|window\.location).*(gumroad|purchase)", re.IGNORECASE)],
        )
        if not redirect_hits and status == "PASS":
            status = "RISK"
            details.append("Could not find redirect helper signal for purchase flow.")
            recommendations.append("Confirm purchase CTA still uses existing Gumroad redirect helper.")

        cta_hits = find_regex_occurrences(
            files,
            [re.compile(r"(unlock full access|full paper|complete mock exam|continue practice)", re.IGNORECASE)],
        )
        if not cta_hits and status == "PASS":
            status = "RISK"
            details.append("No primary purchase CTA language found in static scan.")

        summary = "Purchase flow baseline and static checks passed."
        if status == "FAIL":
            summary = "Purchase flow regression detected."
        elif status == "RISK":
            summary = "Purchase flow has risk signals requiring manual review."
        elif status == "NEEDS_MANUAL_CHECK":
            summary = "Purchase flow baseline requires initial manual approval."
        return self.result(
            status=status,
            summary=summary,
            details=details,
            files_checked=files_checked,
            recommendations=recommendations,
        )
