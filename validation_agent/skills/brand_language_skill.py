from __future__ import annotations

import re
from pathlib import Path

from validation_agent.skills.base import BaseSkill
from validation_agent.skills.checks import (
    find_regex_occurrences,
    format_hit,
    load_simple_yaml,
    repo_root,
    workspace_root,
)


class BrandLanguageSkill(BaseSkill):
    skill_name = "Brand Language"

    def run(self):
        config_path = repo_root() / "validation_agent" / "skill_config" / "banned_terms.yml"
        config = load_simple_yaml(config_path)
        banned_terms = [str(item) for item in config.get("banned_terms", [])]
        allowlist = {str(item).lower() for item in config.get("allowlist", [])}
        preferred_terms = [str(item) for item in config.get("preferred_terms", [])]

        frontend_root = workspace_root() / "growth-leap-studio" / "src"
        files_checked = [str(frontend_root), str(config_path)]
        details: list[str] = []
        recommendations: list[str] = []
        status = "PASS"

        if not frontend_root.exists():
            return self.result(
                status="NEEDS_MANUAL_CHECK",
                summary="Frontend source folder not found for brand language scan.",
                details=[f"Missing frontend root: {frontend_root}"],
                files_checked=files_checked,
                recommendations=["Run this skill where growth-leap-studio/src is available."],
            )

        files = _iter_user_facing_frontend_files(frontend_root)

        filtered_hits = find_banned_term_hits(files, banned_terms, allowlist)

        if filtered_hits:
            status = "FAIL"
            details.extend([f"Banned term found: {format_hit(*hit)}" for hit in filtered_hits[:40]])
            recommendations.append("Replace banned terms with approved brand language.")

        if preferred_terms:
            details.append(f"Preferred terms reference: {preferred_terms}")

        summary = "No banned brand-language terms found in frontend user-facing source."
        if status == "FAIL":
            summary = "Banned brand-language terms detected."
        return self.result(
            status=status,
            summary=summary,
            details=details,
            files_checked=files_checked,
            recommendations=recommendations,
        )


def _iter_user_facing_frontend_files(frontend_root: Path) -> list[Path]:
    targets = [frontend_root / "pages", frontend_root / "components"]
    files: list[Path] = []
    for target in targets:
        if not target.exists():
            continue
        for path in target.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".ts", ".tsx", ".js", ".jsx", ".md"}:
                continue
            files.append(path)
    return files


def find_banned_term_hits(files: list[Path], banned_terms: list[str], allowlist: set[str]):
    patterns = [re.compile(re.escape(term), re.IGNORECASE) for term in banned_terms]
    hits = find_regex_occurrences(files, patterns)
    filtered_hits = []
    for hit in hits:
        _, _, line = hit
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if line.lower() in allowlist:
            continue
        filtered_hits.append(hit)
    return filtered_hits
