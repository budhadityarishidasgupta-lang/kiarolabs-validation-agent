import json
from datetime import datetime, timezone
from pathlib import Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_summary(results: list[dict]) -> dict:
    counts = {"passed": 0, "failed": 0, "skipped": 0, "warned": 0}
    by_module = {}
    by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}

    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
        module = result.get("module", "general")
        module_bucket = by_module.setdefault(
            module,
            {"passed": 0, "failed": 0, "skipped": 0, "warned": 0, "results": []},
        )
        module_bucket[result["status"]] = module_bucket.get(result["status"], 0) + 1
        module_bucket["results"].append(result)

        severity = result.get("severity")
        if severity in by_severity and result["status"] in {"failed", "warned"}:
            by_severity[severity] += 1

    return {
        "generated_at": _utc_now_iso(),
        "counts": counts,
        "by_module": by_module,
        "by_severity": by_severity,
        "results": results,
    }


def write_json_report(report: dict, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "validation-latest.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def write_markdown_report(report: dict, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "validation-latest.md"

    lines = [
        "# Validation Agent Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Passed: `{report['counts'].get('passed', 0)}`",
        f"- Failed: `{report['counts'].get('failed', 0)}`",
        f"- Warned: `{report['counts'].get('warned', 0)}`",
        f"- Skipped: `{report['counts'].get('skipped', 0)}`",
        f"- Critical findings: `{report.get('by_severity', {}).get('CRITICAL', 0)}`",
        f"- High findings: `{report.get('by_severity', {}).get('HIGH', 0)}`",
        f"- Medium findings: `{report.get('by_severity', {}).get('MEDIUM', 0)}`",
        "",
        "## Results By Module",
        "",
    ]

    for module_name, module_data in sorted(report.get("by_module", {}).items()):
        lines.append(f"### {module_name}")
        lines.append("")
        lines.append(f"- Passed: `{module_data.get('passed', 0)}`")
        lines.append(f"- Failed: `{module_data.get('failed', 0)}`")
        lines.append(f"- Warned: `{module_data.get('warned', 0)}`")
        lines.append(f"- Skipped: `{module_data.get('skipped', 0)}`")
        lines.append("")

        for result in module_data.get("results", []):
            lines.append(f"#### {result['name']}")
            lines.append("")
            lines.append(f"- Status: `{result['status']}`")
            if result.get("severity"):
                lines.append(f"- Severity: `{result['severity']}`")
            if result.get("validator"):
                lines.append(f"- Validator: `{result['validator']}`")
            if result.get("detail"):
                lines.append(f"- Detail: `{result['detail']}`")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
