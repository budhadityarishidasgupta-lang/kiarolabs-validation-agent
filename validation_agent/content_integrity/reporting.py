from __future__ import annotations

import json
from pathlib import Path

from .audit import ContentAuditReport


def write_content_audit_report(report: ContentAuditReport, reports_dir: str | Path) -> tuple[Path, Path]:
    target = Path(reports_dir)
    target.mkdir(parents=True, exist_ok=True)
    slug = report.app.lower().replace(" ", "-")
    json_path = target / f"content-integrity-{slug}.json"
    md_path = target / f"content-integrity-{slug}.md"
    payload = report.to_dict()
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    severity_counts: dict[str, int] = {}
    for anomaly in report.anomalies:
        severity_counts[anomaly.severity] = severity_counts.get(anomaly.severity, 0) + 1

    lines = [
        f"# {report.app} Content Integrity Audit",
        "",
        f"- Source: `{report.source}`",
        f"- Records checked: **{report.records_checked}**",
        f"- Records without CRITICAL/HIGH anomalies: **{report.passed_records}**",
        f"- Records with CRITICAL/HIGH anomalies: **{report.records_checked - report.passed_records}**",
        f"- Anomalies: **{len(report.anomalies)}**",
        "",
        "## Severity summary",
        "",
    ]
    if severity_counts:
        lines.extend(f"- {severity}: {count}" for severity, count in sorted(severity_counts.items()))
    else:
        lines.append("- No anomalies detected.")

    lines.extend(["", "## Anomalies", ""])
    if not report.anomalies:
        lines.append("No anomalies detected.")
    else:
        lines.append("| Severity | Item | Code | Finding |")
        lines.append("|---|---|---|---|")
        for anomaly in report.anomalies:
            message = anomaly.message.replace("|", "\\|")
            lines.append(f"| {anomaly.severity} | {anomaly.item_id} | {anomaly.code} | {message} |")

    lines.extend(["", "## Answer distribution", ""])
    if report.answer_distribution:
        for answer, count in sorted(report.answer_distribution.items()):
            lines.append(f"- `{answer}`: {count}")
    else:
        lines.append("No answer distribution available.")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path
