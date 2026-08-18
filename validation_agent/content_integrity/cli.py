from __future__ import annotations

import argparse

from .audit import audit_content_file
from .reporting import write_content_audit_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Kiarolabs learning-content integrity audit")
    parser.add_argument("--app", required=True, help="Explicit learning app name; audits must be run one app at a time")
    parser.add_argument("--source", required=True, help="App-specific CSV or JSON content export")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--fail-on-high", action="store_true")
    args = parser.parse_args()

    report = audit_content_file(args.source, app=args.app)
    json_path, md_path = write_content_audit_report(report, args.reports_dir)
    print(f"Checked {report.records_checked} records for {report.app}.")
    print(f"PASS records: {report.passed_records}")
    print(f"Anomalies: {len(report.anomalies)}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")

    if args.fail_on_high and any(item.severity in {"CRITICAL", "HIGH"} for item in report.anomalies):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
