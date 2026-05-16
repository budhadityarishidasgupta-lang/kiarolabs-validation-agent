from __future__ import annotations

from dataclasses import dataclass

from validation_agent.client import ApiClient, LoginContext
from validation_agent.reporting import TestResult


@dataclass(frozen=True)
class SaleScenario:
    test_id: str
    product_name: str
    product_permalink: str
    product_url: str | None
    expected_app_code: str | None


ONLINE_PRACTICE_SALES: list[SaleScenario] = [
    SaleScenario(
        test_id="test_gumroad_sale_mathsprint_unlocks_only_math",
        product_name="MathSprint",
        product_permalink="ztwxby",
        product_url=None,
        expected_app_code="math",
    ),
    SaleScenario(
        test_id="test_gumroad_sale_spellingsprint_unlocks_only_spelling",
        product_name="SpellingSprint",
        product_permalink="gxvtls",
        product_url=None,
        expected_app_code="spelling",
    ),
    SaleScenario(
        test_id="test_gumroad_sale_wordsprint_unlocks_only_general",
        product_name="WordSprint",
        product_permalink="sddokb",
        product_url=None,
        expected_app_code="general",
    ),
    SaleScenario(
        test_id="test_gumroad_sale_comprehensionsprint_unlocks_only_comprehension",
        product_name="ComprehensionSprint",
        product_permalink="gckvb",
        product_url=None,
        expected_app_code="comprehension",
    ),
]

ONLINE_PRACTICE_PRODUCT_URL_SALES: list[SaleScenario] = [
    SaleScenario(
        test_id="test_gumroad_sale_product_url_mathsprint_unlocks_only_math",
        product_name="MathSprint",
        product_permalink="",
        product_url="https://kiarolabs.gumroad.com/l/ztwxby",
        expected_app_code="math",
    ),
    SaleScenario(
        test_id="test_gumroad_sale_product_url_spellingsprint_unlocks_only_spelling",
        product_name="SpellingSprint",
        product_permalink="",
        product_url="https://kiarolabs.gumroad.com/l/gxvtls",
        expected_app_code="spelling",
    ),
    SaleScenario(
        test_id="test_gumroad_sale_product_url_wordsprint_unlocks_only_general",
        product_name="WordSprint",
        product_permalink="",
        product_url="https://kiarolabs.gumroad.com/l/sddokb",
        expected_app_code="general",
    ),
    SaleScenario(
        test_id="test_gumroad_sale_product_url_comprehensionsprint_unlocks_only_comprehension",
        product_name="ComprehensionSprint",
        product_permalink="",
        product_url="https://kiarolabs.gumroad.com/l/gckvb",
        expected_app_code="comprehension",
    ),
]

PRINTABLE_SALES: list[SaleScenario] = [
    SaleScenario(
        test_id="test_gumroad_sale_comprehension_printable_does_not_unlock_online_practice",
        product_name="English Comprehension – 11+ Exam Preparation (3)",
        product_permalink="rbtolw",
        product_url=None,
        expected_app_code=None,
    ),
    SaleScenario(
        test_id="test_gumroad_sale_vr_printable_does_not_unlock_online_practice",
        product_name="Verbal Reasoning Practice Paper 03",
        product_permalink="nsfah",
        product_url=None,
        expected_app_code=None,
    ),
]

MOCK_SALES: list[SaleScenario] = [
    SaleScenario(
        test_id="test_gumroad_sale_mock_1_unlocks_only_mock_1",
        product_name="Maths Mock Exam 1 - 11+ Exam Preparation",
        product_permalink="zqwlsf",
        product_url=None,
        expected_app_code=None,
    ),
]

IGNORED_PRODUCT_SALES: list[SaleScenario] = [
    SaleScenario(
        test_id="test_gumroad_sale_disabled_bundle_unlocks_nothing",
        product_name="Maths Mock Pack (6 Tests)",
        product_permalink="akizdp",
        product_url=None,
        expected_app_code=None,
    ),
    SaleScenario(
        test_id="test_gumroad_sale_unknown_product_unlocks_nothing",
        product_name="Unknown Product For Validation",
        product_permalink="unknown-permalink",
        product_url=None,
        expected_app_code=None,
    ),
]


def _webhook_sale(
    client: ApiClient,
    *,
    email: str,
    product_name: str,
    product_permalink: str,
    product_url: str | None = None,
) -> dict:
    payload = {
        "email": email,
        "product_name": product_name,
        "event": "sale",
        "sale_id": f"validation-{product_permalink or product_url or product_name}",
    }
    if product_permalink:
        payload["product_permalink"] = product_permalink
    if product_url:
        payload["product_url"] = product_url
    return client.request_json(
        "POST",
        "/webhook/gumroad",
        data=payload,
    )


def _set_user_apps(client: ApiClient, admin: LoginContext, student_email: str, apps: list[str]) -> dict:
    return client.request_json(
        "POST",
        "/admin/set-user-apps",
        token=admin.token,
        json={
            "email": student_email,
            "apps": apps,
        },
    )


def _get_user_apps(client: ApiClient, admin: LoginContext, student_email: str) -> list[str]:
    payload = client.request_json(
        "GET",
        f"/admin/user-apps?email={student_email}",
        token=admin.token,
    )
    apps = payload.get("apps") or []
    return sorted(str(app).strip().lower() for app in apps if app)


def _assert_only_expected_online_practice(apps: list[str], expected_app: str | None) -> tuple[bool, dict]:
    online_practice_codes = {"math", "spelling", "general", "comprehension"}
    present_online_codes = sorted(app for app in apps if app in online_practice_codes)
    if expected_app is None:
        return (len(present_online_codes) == 0), {"online_practice_codes": present_online_codes}
    return (present_online_codes == [expected_app]), {"online_practice_codes": present_online_codes}


def _modules_from_dashboard(payload: dict) -> dict:
    modules = payload.get("modules") or {}
    return {
        "math": bool((modules.get("math") or modules.get("maths") or {}).get("unlocked")),
        "spelling": bool((modules.get("spelling") or {}).get("unlocked")),
        "general": bool((modules.get("words") or {}).get("unlocked")),
        "comprehension": bool((modules.get("comprehension") or {}).get("unlocked")),
    }


def run_gumroad_entitlement_validation(
    *,
    client: ApiClient,
    admin_email: str,
    admin_password: str,
    student_email: str | None,
    student_password: str | None,
) -> list[TestResult]:
    if not student_email or not student_password:
        return [
            TestResult(
                test_id="test_gumroad_entitlement_validation_prerequisites",
                status="skip",
                message="Set VALIDATION_STUDENT_EMAIL and VALIDATION_STUDENT_PASSWORD to run Gumroad entitlement tests.",
            )
        ]

    admin = client.login(admin_email, admin_password)
    student = client.login(student_email, student_password)
    results: list[TestResult] = []

    all_scenarios = ONLINE_PRACTICE_SALES + ONLINE_PRACTICE_PRODUCT_URL_SALES + PRINTABLE_SALES
    for scenario in all_scenarios:
        try:
            _set_user_apps(client, admin, student_email, [])
            _webhook_sale(
                client,
                email=student_email,
                product_name=scenario.product_name,
                product_permalink=scenario.product_permalink,
                product_url=scenario.product_url,
            )
            apps = _get_user_apps(client, admin, student_email)

            ok, details = _assert_only_expected_online_practice(apps, scenario.expected_app_code)
            if not ok:
                expected = scenario.expected_app_code if scenario.expected_app_code else "none"
                results.append(
                    TestResult(
                        test_id=scenario.test_id,
                        status="fail",
                        message=f"{scenario.product_name}: expected online-practice unlock '{expected}', got {details['online_practice_codes']}",
                        details={"apps": apps, **details},
                    )
                )
                continue

            results.append(
                TestResult(
                    test_id=scenario.test_id,
                    status="pass",
                    message=f"{scenario.product_name}: webhook unlock behavior matched expected online-practice entitlement",
                    details={"apps": apps, **details},
                )
            )
        except Exception as exc:
            results.append(
                TestResult(
                    test_id=scenario.test_id,
                    status="fail",
                    message=f"{scenario.product_name}: Gumroad entitlement simulation failed",
                    details={"error": str(exc)},
                )
            )

    # Printable sale should create per-paper purchased state and keep online-practice unchanged.
    for scenario in PRINTABLE_SALES:
        try:
            _set_user_apps(client, admin, student_email, [])
            _webhook_sale(
                client,
                email=student_email,
                product_name=scenario.product_name,
                product_permalink=scenario.product_permalink,
                product_url=scenario.product_url,
            )
            purchases = client.request_json("GET", "/purchases/printables", token=student.token)
            purchased_permalinks = set((purchases.get("purchased_permalinks") or []))
            if scenario.product_permalink not in purchased_permalinks:
                results.append(
                    TestResult(
                        test_id=f"{scenario.test_id}_purchased_state",
                        status="fail",
                        message=f"{scenario.product_name}: expected purchased permalink {scenario.product_permalink}",
                        details={"purchases": purchases},
                    )
                )
            else:
                results.append(
                    TestResult(
                        test_id=f"{scenario.test_id}_purchased_state",
                        status="pass",
                        message=f"{scenario.product_name}: purchased state contains expected permalink.",
                    )
                )
        except Exception as exc:
            results.append(
                TestResult(
                    test_id=f"{scenario.test_id}_purchased_state",
                    status="fail",
                    message="Failed printable purchased-state validation.",
                    details={"error": str(exc)},
                )
            )

    # Disabled/unknown products should unlock nothing.
    for scenario in IGNORED_PRODUCT_SALES:
        try:
            _set_user_apps(client, admin, student_email, [])
            _webhook_sale(
                client,
                email=student_email,
                product_name=scenario.product_name,
                product_permalink=scenario.product_permalink,
                product_url=scenario.product_url,
            )
            apps = _get_user_apps(client, admin, student_email)
            ok, details = _assert_only_expected_online_practice(apps, None)
            if not ok:
                results.append(
                    TestResult(
                        test_id=scenario.test_id,
                        status="fail",
                        message=f"{scenario.product_name}: expected no online-practice unlocks",
                        details={"apps": apps, **details},
                    )
                )
            else:
                results.append(
                    TestResult(
                        test_id=scenario.test_id,
                        status="pass",
                        message=f"{scenario.product_name}: no online-practice unlock created.",
                    )
                )
        except Exception as exc:
            results.append(
                TestResult(
                    test_id=scenario.test_id,
                    status="fail",
                    message=f"{scenario.product_name}: ignored-product validation failed",
                    details={"error": str(exc)},
                )
            )

    # Mock purchase should unlock only matching mock test id.
    for scenario in MOCK_SALES:
        try:
            _set_user_apps(client, admin, student_email, [])
            _webhook_sale(
                client,
                email=student_email,
                product_name=scenario.product_name,
                product_permalink=scenario.product_permalink,
                product_url=scenario.product_url,
            )
            start_ok = client.request_json(
                "GET",
                "/practice/math/test/start?test_id=MATH_MOCK_1",
                token=student.token,
            )
            access_mode = str(start_ok.get("access_mode") or "").lower()
            wrong_mock_denied = False
            try:
                client.request_json(
                    "GET",
                    "/practice/math/test/start?test_id=MATH_MOCK_2",
                    token=student.token,
                )
            except Exception:
                wrong_mock_denied = True

            if access_mode != "full" or not wrong_mock_denied:
                results.append(
                    TestResult(
                        test_id=scenario.test_id,
                        status="fail",
                        message="Mock purchase did not enforce one-to-one unlock behavior.",
                        details={
                            "mock_1_access_mode": access_mode,
                            "mock_2_denied": wrong_mock_denied,
                        },
                    )
                )
            else:
                results.append(
                    TestResult(
                        test_id=scenario.test_id,
                        status="pass",
                        message="Mock purchase unlocks only the matching mock test.",
                    )
                )
        except Exception as exc:
            results.append(
                TestResult(
                    test_id=scenario.test_id,
                    status="fail",
                    message="Mock one-to-one unlock validation failed.",
                    details={"error": str(exc)},
                )
            )

    # Webhook replay should be idempotent for online practice module unlock.
    try:
        _set_user_apps(client, admin, student_email, [])
        replay = ONLINE_PRACTICE_SALES[0]
        _webhook_sale(
            client,
            email=student_email,
            product_name=replay.product_name,
            product_permalink=replay.product_permalink,
            product_url=replay.product_url,
        )
        _webhook_sale(
            client,
            email=student_email,
            product_name=replay.product_name,
            product_permalink=replay.product_permalink,
            product_url=replay.product_url,
        )
        apps = _get_user_apps(client, admin, student_email)
        online_codes = sorted(code for code in apps if code in {"math", "spelling", "general", "comprehension"})
        if online_codes != ["math"]:
            results.append(
                TestResult(
                    test_id="test_gumroad_webhook_replay_idempotent",
                    status="fail",
                    message="Webhook replay created unexpected module unlock state.",
                    details={"online_codes": online_codes, "apps": apps},
                )
            )
        else:
            results.append(
                TestResult(
                    test_id="test_gumroad_webhook_replay_idempotent",
                    status="pass",
                    message="Webhook replay is idempotent for module entitlement.",
                )
            )
    except Exception as exc:
        results.append(
            TestResult(
                test_id="test_gumroad_webhook_replay_idempotent",
                status="fail",
                message="Failed to validate webhook replay idempotency.",
                details={"error": str(exc)},
            )
        )

    # Additional explicit check: math-only user should not see all modules open.
    try:
        _set_user_apps(client, admin, student_email, ["math"])
        dashboard_payload = client.request_json("GET", "/dashboard", token=student.token)
        practice_dashboard_payload = client.request_json("GET", "/practice/dashboard", token=student.token)

        dashboard_unlocks = _modules_from_dashboard(dashboard_payload)
        practice_unlocks = _modules_from_dashboard(practice_dashboard_payload)

        expected_unlocks = {
            "math": True,
            "spelling": False,
            "general": False,
            "comprehension": False,
        }
        dashboard_ok = dashboard_unlocks == expected_unlocks
        practice_ok = practice_unlocks == expected_unlocks

        if not dashboard_ok or not practice_ok:
            results.append(
                TestResult(
                    test_id="test_math_only_user_does_not_see_all_modules_open",
                    status="fail",
                    message="Math-only student should not see all modules unlocked.",
                    details={
                        "expected": expected_unlocks,
                        "dashboard": dashboard_unlocks,
                        "practice_dashboard": practice_unlocks,
                    },
                )
            )
        else:
            results.append(
                TestResult(
                    test_id="test_math_only_user_does_not_see_all_modules_open",
                    status="pass",
                    message="Math-only student sees only MathSprint unlocked in both dashboard endpoints.",
                )
            )
    except Exception as exc:
        results.append(
            TestResult(
                test_id="test_math_only_user_does_not_see_all_modules_open",
                status="fail",
                message="Failed to validate math-only dashboard unlock contract.",
                details={"error": str(exc)},
            )
        )

    # Runtime enforcement check: direct full-access routes should be denied for non-entitled modules.
    try:
        _set_user_apps(client, admin, student_email, ["math"])

        math_lessons = client.request_json("GET", "/practice/math/lessons", token=student.token)
        if not isinstance(math_lessons, list):
            raise RuntimeError("Expected /practice/math/lessons to return a list")

        denied_paths = [
            "/practice/words/courses",
            "/practice/spelling/courses",
            "/practice/comprehension/passages",
        ]
        denied_results = {}
        for path in denied_paths:
            try:
                client.request_json("GET", path, token=student.token)
                denied_results[path] = "unexpected_success"
            except Exception as exc:
                denied_results[path] = str(exc)

        if any(value == "unexpected_success" for value in denied_results.values()):
            results.append(
                TestResult(
                    test_id="test_runtime_enforcement_math_only_routes",
                    status="fail",
                    message="Math-only student unexpectedly reached one or more non-entitled full-access routes.",
                    details=denied_results,
                )
            )
        else:
            results.append(
                TestResult(
                    test_id="test_runtime_enforcement_math_only_routes",
                    status="pass",
                    message="Math-only student can access MathSprint route while non-entitled full-access routes are denied.",
                )
            )
    except Exception as exc:
        results.append(
            TestResult(
                test_id="test_runtime_enforcement_math_only_routes",
                status="fail",
                message="Failed to validate route-level enforcement for math-only user.",
                details={"error": str(exc)},
            )
        )

    # Stale-session check: revocation must apply immediately for existing token (no re-login).
    try:
        _set_user_apps(client, admin, student_email, ["general"])
        client.request_json("GET", "/practice/words/courses", token=student.token)

        _set_user_apps(client, admin, student_email, ["math"])
        revoked_denied = False
        try:
            client.request_json("GET", "/practice/words/courses", token=student.token)
        except Exception:
            revoked_denied = True

        if revoked_denied:
            results.append(
                TestResult(
                    test_id="test_stale_session_revocation_enforced_immediately",
                    status="pass",
                    message="WordSprint access revocation applied immediately for existing student token.",
                )
            )
        else:
            results.append(
                TestResult(
                    test_id="test_stale_session_revocation_enforced_immediately",
                    status="fail",
                    message="Revoked WordSprint access still succeeded with stale session token.",
                )
            )
    except Exception as exc:
        results.append(
            TestResult(
                test_id="test_stale_session_revocation_enforced_immediately",
                status="fail",
                message="Failed stale-session revocation enforcement check.",
                details={"error": str(exc)},
            )
        )

    return results
