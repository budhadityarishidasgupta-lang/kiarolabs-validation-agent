import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

from validation_agent.config import REPORTS_DIR


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_reports(report: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "db-verification-latest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# DB Verification Report",
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
    (REPORTS_DIR / "db-verification-latest.md").write_text("\n".join(lines), encoding="utf-8")


def _build_report(results: list[dict]) -> dict:
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    return {
        "generated_at": _utc_now_iso(),
        "counts": counts,
        "results": results,
    }


def _load_artifacts(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def run_db_verification() -> dict:
    results = []
    mutations_enabled = os.getenv("E2E_ENABLE_MUTATIONS", "false").lower() == "true"
    dsn = os.getenv("VALIDATION_DB_DSN", "").strip()
    artifacts = _load_artifacts(REPORTS_DIR / "mutation-artifacts.json")

    if not mutations_enabled:
        results.append({"name": "db_verification", "status": "skipped", "detail": "Mutation mode disabled"})
        report = _build_report(results)
        _write_reports(report)
        return report

    if not dsn:
        results.append({"name": "db_verification", "status": "skipped", "detail": "VALIDATION_DB_DSN not configured"})
        report = _build_report(results)
        _write_reports(report)
        return report

    if not artifacts:
        results.append({"name": "db_verification", "status": "skipped", "detail": "No mutation artifacts found"})
        report = _build_report(results)
        _write_reports(report)
        return report

    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    try:
        for artifact in artifacts:
            kind = artifact.get("kind")
            payload = artifact.get("payload", {})

            try:
                if kind == "maths_lesson_create":
                    if payload.get("cleaned_up"):
                        results.append({"name": f"db_{kind}", "status": "skipped", "detail": "Maths lesson cleaned up after validation"})
                        continue
                    cur.execute(
                        """
                        SELECT lesson_code
                        FROM math_lessons
                        WHERE display_name = %s
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (payload.get("display_name"),),
                    )
                    row = cur.fetchone()
                    assert row and row[0], "Maths lesson not found"
                    results.append({"name": f"db_{kind}", "status": "passed", "detail": payload.get("display_name", "")})

                elif kind in {"comprehension_csv_upload", "comprehension_pdf_upload"}:
                    cur.execute(
                        """
                        SELECT passage_id
                        FROM comprehension_passages
                        WHERE title = %s
                        ORDER BY passage_id DESC
                        LIMIT 1
                        """,
                        (payload.get("title"),),
                    )
                    row = cur.fetchone()
                    assert row and row[0], "Comprehension passage not found"
                    results.append({"name": f"db_{kind}", "status": "passed", "detail": payload.get("title", "")})

                elif kind == "printable_answer_key_save":
                    cur.execute(
                        """
                        SELECT COUNT(*), MAX(CASE WHEN question_number = 1 THEN correct_answer END)
                        FROM math_printable_answer_keys
                        WHERE paper_code = %s
                        """,
                        (payload.get("paper_code"),),
                    )
                    row = cur.fetchone()
                    assert row and row[0] >= int(payload.get("answers_saved") or 0), "Printable answer count mismatch"
                    if payload.get("first_answer"):
                        assert row[1] == payload.get("first_answer"), "Printable first answer mismatch"
                    results.append({"name": f"db_{kind}", "status": "passed", "detail": payload.get("paper_code", "")})
            except Exception as exc:
                results.append({"name": f"db_{kind}", "status": "failed", "detail": str(exc)})
    finally:
        cur.close()
        conn.close()

    report = _build_report(results)
    _write_reports(report)
    return report


if __name__ == "__main__":
    report = run_db_verification()
    raise SystemExit(0 if report["counts"].get("failed", 0) == 0 else 1)
