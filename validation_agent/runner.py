import pytest

from validation_agent.tests.test_admin_access import test_admin_unlocks_all
from validation_agent.tests.test_auth import (
    test_login,
    test_login_invalid,
    test_repeat_login_stress,
)
from validation_agent.tests.test_dashboard import (
    test_dashboard_admin_unlocks_all_modules,
    test_dashboard_loads,
    test_no_token_dashboard,
)
from validation_agent.tests.test_spelling import test_spelling_question_retrieval
from validation_agent.tests.test_words import test_invalid_word_submission, test_words_submission


def run_all():
    print("Running Validation Agent...\n")

    tests = [
        test_login,
        test_repeat_login_stress,
        test_login_invalid,
        test_admin_unlocks_all,
        test_no_token_dashboard,
        test_spelling_question_retrieval,
        test_words_submission,
        test_invalid_word_submission,
        test_dashboard_loads,
        test_dashboard_admin_unlocks_all_modules,
    ]

    for test in tests:
        try:
            test()
            print(f"[PASS] {test.__name__}")
        except pytest.skip.Exception as e:
            print(f"[SKIP] {test.__name__}: {e}")
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")

    print("\nDone.")


if __name__ == "__main__":
    run_all()
