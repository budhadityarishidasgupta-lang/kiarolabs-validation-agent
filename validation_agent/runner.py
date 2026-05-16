from __future__ import annotations

import sys

from validation_agent.client import ApiClient
from validation_agent.config import load_settings
from validation_agent.reporting import (
    summarize,
    write_reports,
    write_skill_report,
    write_learning_accuracy_reports,
)
from validation_agent.accuracy import run_accuracy_audit
from validation_agent.skills import run_skill_suite
from validation_agent.tests.gumroad_entitlements import run_gumroad_entitlement_validation
from validation_agent.tests.vr_printables import run_vr_printable_validation


def run_all() -> int:
    settings = load_settings()
    skill_results = run_skill_suite()
    latest_skill_report = write_skill_report(skill_results, settings.reports_dir)

    results = []
    if settings.admin_email and settings.admin_password:
        client = ApiClient(settings.base_url, settings.request_timeout_seconds)
        try:
            results = run_vr_printable_validation(
                client=client,
                admin_email=settings.admin_email,
                admin_password=settings.admin_password,
                student_email=settings.student_email,
                student_password=settings.student_password,
                keys_dir=settings.vr_keys_dir,
            )
            results.extend(
                run_gumroad_entitlement_validation(
                    client=client,
                    admin_email=settings.admin_email,
                    admin_password=settings.admin_password,
                    student_email=settings.student_email,
                    student_password=settings.student_password,
                )
            )
        finally:
            client.close()
    else:
        print("[SKIP] Runtime API smoke tests skipped: set VALIDATION_ADMIN_EMAIL and VALIDATION_ADMIN_PASSWORD.")

    report = summarize(results)
    json_path, md_path = write_reports(report, settings.reports_dir)
    accuracy_report = run_accuracy_audit(settings)
    accuracy_json_path, accuracy_md_path, manus_tasks_path = write_learning_accuracy_reports(
        accuracy_report,
        settings.reports_dir,
    )

    print("Skill checks:")
    for result in skill_results:
        print(f"[{result.status}] {result.skill_name}: {result.summary}")
    print("")

    for result in results:
        print(f"[{result.status.upper()}] {result.test_id}: {result.message}")
    print("")
    print("Reports:")
    print(f"- {json_path}")
    print(f"- {md_path}")
    print(f"- {latest_skill_report}")
    print(f"- {accuracy_json_path}")
    print(f"- {accuracy_md_path}")
    print(f"- {manus_tasks_path}")

    if (
        settings.fail_on_failure
        and (
            report.failed
            or any(result.status == "FAIL" for result in skill_results)
        )
    ):
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
