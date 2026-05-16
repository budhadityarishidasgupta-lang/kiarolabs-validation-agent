from __future__ import annotations

from pathlib import Path

from validation_agent.accuracy.audit_runner import run_accuracy_audit
from validation_agent.accuracy.types import AccuracyFinding, ManusReviewTask
from validation_agent.config import Settings
from validation_agent.reporting import write_learning_accuracy_reports


def test_accuracy_finding_shape():
    finding = AccuracyFinding(
        product="MathSprint",
        lesson_or_paper_id="1",
        question_id="Q1",
        status="PASS",
        reason="ok",
        evidence="sample",
        suggested_human_review_note="review",
    )
    payload = finding.to_dict()
    assert payload["product"] == "MathSprint"
    assert payload["status"] == "PASS"


def test_manus_task_shape():
    task = ManusReviewTask(
        url="https://example.com",
        login_role_needed="admin",
        product="Admin flow",
        lesson_or_paper="purchase_tracking",
        what_manus_should_inspect="filters",
        expected_behaviour="works",
        screenshot_requirement="capture table",
    )
    payload = task.to_dict()
    assert payload["login_role_needed"] == "admin"


def test_learning_accuracy_report_files(tmp_path: Path):
    settings = Settings(
        base_url="https://example.com",
        admin_email=None,
        admin_password=None,
        student_email=None,
        student_password=None,
        reports_dir=tmp_path,
        vr_keys_dir=tmp_path,
        request_timeout_seconds=1.0,
        fail_on_failure=False,
    )
    report = run_accuracy_audit(settings)
    json_path, md_path, manus_path = write_learning_accuracy_reports(report, tmp_path)
    assert json_path.exists()
    assert md_path.exists()
    assert manus_path.exists()
    assert "learning_accuracy_report" in json_path.name
    assert "manus_review_tasks" in manus_path.name

