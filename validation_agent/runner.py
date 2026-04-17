from tests.test_auth import test_login
from tests.test_admin_access import test_admin_unlocks_all
from tests.test_spelling import test_spelling_attempt_recorded
from tests.test_words import test_words_submission
from tests.test_dashboard import test_dashboard_loads, test_dashboard_admin_unlocks_all_modules

def run_all():
    print("Running Validation Agent...\n")

    tests = [
        test_login,
        test_admin_unlocks_all,
        test_spelling_attempt_recorded,
        test_words_submission,
        test_dashboard_loads,
        test_dashboard_admin_unlocks_all_modules
    ]

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")

    print("\nDone.")

if __name__ == "__main__":
    run_all()