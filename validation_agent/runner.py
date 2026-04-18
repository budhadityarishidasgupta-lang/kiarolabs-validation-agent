import sys

import pytest

from validation_agent.config import FAIL_ON_FAILURE, REPORTS_DIR
from validation_agent.reporting import build_summary, write_json_report, write_markdown_report
from validation_agent.tests.test_admin_access import test_admin_unlocks_all
from validation_agent.tests.test_auth import (
    test_admin_role_consistency,
    test_login,
    test_login_invalid,
    test_repeat_login_stress,
)
from validation_agent.tests.test_dashboard import (
    test_dashboard_admin_unlocks_all_modules,
    test_dashboard_loads,
    test_no_token_dashboard,
)
from validation_agent.tests.test_math_submission import test_math_submission
from validation_agent.tests.test_math_tests import (
    test_admin_can_start_mock_test_without_purchase_check,
    test_math_paper_submission_returns_score,
)
from validation_agent.tests.test_password_reset import (
    test_admin_reset_password_requires_token,
    test_direct_reset_does_not_expose_user_existence,
    test_request_reset_does_not_expose_user_existence,
    test_reset_password_rejects_invalid_token,
)
from validation_agent.tests.test_spelling import test_spelling_question_retrieval
from validation_agent.tests.test_words import test_invalid_word_submission, test_words_submission


TESTS = [
    test_login,
    test_repeat_login_stress,
    test_login_invalid,
    test_admin_role_consistency,
    test_admin_unlocks_all,
    test_no_token_dashboard,
    test_request_reset_does_not_expose_user_existence,
    test_reset_password_rejects_invalid_token,
    test_direct_reset_does_not_expose_user_existence,
    test_admin_reset_password_requires_token,
    test_admin_can_start_mock_test_without_purchase_check,
    test_math_paper_submission_returns_score,
    test_math_submission,
    test_spelling_question_retrieval,
    test_words_submission,
    test_invalid_word_submission,
    test_dashboard_loads,
    test_dashboard_admin_unlocks_all_modules,
]


def run_all():
    print("Running Validation Agent...\n")
    results = []

    for test in TESTS:
        try:
            test()
            print(f"[PASS] {test.__name__}")
            results.append({"name": test.__name__, "status": "passed", "detail": ""})
        except pytest.skip.Exception as e:
            print(f"[SKIP] {test.__name__}: {e}")
            results.append({"name": test.__name__, "status": "skipped", "detail": str(e)})
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            results.append({"name": test.__name__, "status": "failed", "detail": str(e)})

    report = build_summary(results)
    json_path = write_json_report(report, REPORTS_DIR)
    md_path = write_markdown_report(report, REPORTS_DIR)

    print("\nReports:")
    print(f"- {json_path}")
    print(f"- {md_path}")
    print("\nDone.")

    if FAIL_ON_FAILURE and report["counts"].get("failed", 0) > 0:
        raise SystemExit(1)

    return report


if __name__ == "__main__":
    sys.exit(0 if run_all()["counts"].get("failed", 0) == 0 or not FAIL_ON_FAILURE else 1)
