import json
from datetime import datetime, timezone
from pathlib import Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_summary(results: list[dict]) -> dict:
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    return {
        "generated_at": _utc_now_iso(),
        "counts": counts,
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
        f"- Skipped: `{report['counts'].get('skipped', 0)}`",
        "",
        "## Results",
        "",
    ]

    for result in report["results"]:
        lines.append(f"### {result['name']}")
        lines.append("")
        lines.append(f"- Status: `{result['status']}`")
        if result.get("detail"):
            lines.append(f"- Detail: `{result['detail']}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
