from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from validation_agent.skills.base import SkillResult
from validation_agent.accuracy.types import AccuracyAuditReport


@dataclass
class TestResult:
    test_id: str
    status: str
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class RunReport:
    generated_at: str
    passed: int
    failed: int
    skipped: int
    results: list[TestResult]


def summarize(results: list[TestResult]) -> RunReport:
    return RunReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        passed=sum(1 for result in results if result.status == "pass"),
        failed=sum(1 for result in results if result.status == "fail"),
        skipped=sum(1 for result in results if result.status == "skip"),
        results=results,
    )


def write_reports(report: RunReport, reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "validation-latest.json"
    md_path = reports_dir / "validation-latest.md"

    json_path.write_text(
        json.dumps(
            {
                **asdict(report),
                "results": [asdict(result) for result in report.results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "# Validation Report",
        "",
        f"- Generated: `{report.generated_at}`",
        f"- Passed: `{report.passed}`",
        f"- Failed: `{report.failed}`",
        f"- Skipped: `{report.skipped}`",
        "",
    ]
    for result in report.results:
        lines.append(f"## {result.status.upper()} {result.test_id}")
        lines.append("")
        lines.append(result.message)
        if result.details:
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(result.details, indent=2))
            lines.append("```")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def write_skill_report(skill_results: list[SkillResult], reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    latest_path = reports_dir / "latest_report.md"

    section_order = [
        "Architecture Guardrails",
        "Learning Integrity",
        "Preview Access",
        "Mock Security",
        "Purchase Flow",
        "Printable Preview",
        "Brand Language",
        "Manual QA",
    ]
    by_name = {result.skill_name: result for result in skill_results}

    lines = [
        "# Validation Skill Report",
        "",
        f"- Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
    ]

    for name in section_order:
        result = by_name.get(name)
        if not result:
            lines.append(f"## {name}")
            lines.append("")
            lines.append("- Status: `NEEDS_MANUAL_CHECK`")
            lines.append("- Summary: Not executed.")
            lines.append("")
            continue

        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- Status: `{result.status}`")
        lines.append(f"- Summary: {result.summary}")
        if result.files_checked:
            lines.append("- Files checked:")
            for path in result.files_checked:
                lines.append(f"  - `{path}`")
        if result.details:
            lines.append("- Details:")
            for item in result.details:
                lines.append(f"  - {item}")
        if result.recommendations:
            lines.append("- Recommended smallest safe fix:")
            for rec in result.recommendations:
                lines.append(f"  - {rec}")
        lines.append("")

    latest_path.write_text("\n".join(lines), encoding="utf-8")
    return latest_path


def write_learning_accuracy_reports(accuracy_report: AccuracyAuditReport, reports_dir: Path) -> tuple[Path, Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "learning_accuracy_report.json"
    md_path = reports_dir / "learning_accuracy_report.md"
    manus_path = reports_dir / "manus_review_tasks.json"

    findings = [item.to_dict() for item in accuracy_report.findings]
    manus_tasks = [task.to_dict() for task in accuracy_report.manus_tasks]

    grouped: dict[str, dict[str, list[dict]]] = {}
    for finding in findings:
        product = finding.get("product", "unknown")
        severity = finding.get("severity", "unknown")
        grouped.setdefault(product, {}).setdefault(severity, []).append(finding)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "findings": len(findings),
            "pass": sum(1 for f in findings if f.get("status") == "PASS"),
            "fail": sum(1 for f in findings if f.get("status") == "FAIL"),
            "risk": sum(1 for f in findings if f.get("status") == "RISK"),
            "needs_review": sum(1 for f in findings if f.get("status") == "NEEDS_REVIEW"),
        },
        "grouped": grouped,
        "findings": findings,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    manus_path.write_text(json.dumps(manus_tasks, indent=2), encoding="utf-8")

    lines = [
        "# Learning Accuracy Report",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Total findings: `{payload['totals']['findings']}`",
        f"- PASS: `{payload['totals']['pass']}`",
        f"- FAIL: `{payload['totals']['fail']}`",
        f"- RISK: `{payload['totals']['risk']}`",
        f"- NEEDS_REVIEW: `{payload['totals']['needs_review']}`",
        "",
    ]
    for product, severity_map in grouped.items():
        lines.append(f"## {product}")
        lines.append("")
        for severity, items in severity_map.items():
            lines.append(f"### Severity: {severity}")
            lines.append("")
            for item in items:
                lines.append(f"- [{item['status']}] `{item['lesson_or_paper_id']}` / `{item['question_id']}`: {item['reason']}")
                lines.append(f"  - Evidence: {item['evidence']}")
                lines.append(f"  - Recommended owner: {item['recommended_owner']}")
                lines.append(f"  - Human review note: {item['suggested_human_review_note']}")
            lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path, manus_path
