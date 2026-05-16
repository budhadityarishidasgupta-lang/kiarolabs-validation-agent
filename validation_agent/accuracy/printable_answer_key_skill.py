from __future__ import annotations

from pathlib import Path

from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.helpers import finding, safe_get_json
from validation_agent.accuracy.types import AccuracyFinding


def run_printable_answer_key_skill(ctx: AuditContext, keys_dir: Path) -> list[AccuracyFinding]:
    findings: list[AccuracyFinding] = []
    papers, err = safe_get_json(ctx, "/practice/verbal-reasoning/printable/papers")
    if err:
        findings.append(
            finding(
                product="Printable papers",
                lesson_or_paper_id="unknown",
                question_id="unknown",
                status="RISK",
                reason="Printable paper list fetch failed",
                evidence=err,
                suggested_human_review_note="Validate printable APIs and rerun answer-key alignment checks.",
                severity="high",
                owner="Codex",
            )
        )
    else:
        findings.append(
            finding(
                product="Printable papers",
                lesson_or_paper_id="vr-printables",
                question_id="n/a",
                status="PASS",
                reason="Printable paper endpoint reachable",
                evidence=f"papers_count={len(papers) if isinstance(papers, list) else 0}",
                suggested_human_review_note="Verify each active paper maps to the correct answer key and upload workflow.",
                severity="low",
                owner="Content Review",
            )
        )
    fixture_count = len(list(keys_dir.glob("*.csv"))) if keys_dir.exists() else 0
    findings.append(
        finding(
            product="Printable papers",
            lesson_or_paper_id="fixtures",
            question_id="n/a",
            status="PASS" if fixture_count > 0 else "NEEDS_REVIEW",
            reason="Approved answer-key fixtures present" if fixture_count > 0 else "No local printable fixtures found",
            evidence=f"fixture_csv_count={fixture_count}, keys_dir={keys_dir}",
            suggested_human_review_note="Keep approved CSV/answer-key snapshots in fixtures for deterministic audits.",
            severity="medium",
            owner="Admin",
        )
    )
    return findings

