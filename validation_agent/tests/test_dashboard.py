from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS


LEARNING_MODULES = {"spelling", "words", "math", "maths", "comprehension"}
ENTITLEMENT_MODULES = {"practice_papers", "vr_printables", "mock_exams", "nvr"}


def _json_object(response, path):
    try:
        data = response.json()
    except Exception as exc:
        raise AssertionError(f"{path} did not return valid JSON: {exc}") from exc

    assert isinstance(data, dict), f"{path} should return a JSON object"
    return data


def _assert_learning_module_contract(module_name, module_data):
    assert isinstance(module_data, dict), f"module '{module_name}' should be an object"
    for key in ("unlocked", "attempts", "accuracy"):
        assert key in module_data, f"module '{module_name}' is missing '{key}'"

    for optional_key in (
        "completion_percent",
        "completed_lessons",
        "total_lessons",
        "status",
        "next_action",
    ):
        if optional_key in module_data:
            module_data[optional_key]


def _assert_entitlement_module_contract(module_name, module_data):
    assert isinstance(module_data, dict), f"module '{module_name}' should be an object"
    assert "unlocked" in module_data, f"module '{module_name}' is missing 'unlocked'"


def _assert_module_contract(module_name, module_data):
    if module_name in LEARNING_MODULES:
        _assert_learning_module_contract(module_name, module_data)
        return

    if module_name in ENTITLEMENT_MODULES:
        _assert_entitlement_module_contract(module_name, module_data)
        return

    _assert_entitlement_module_contract(module_name, module_data)
    print(
        f"VALIDATION WARNING: unknown dashboard module '{module_name}' treated as entitlement/access-only "
        "for contract validation."
    )


def test_dashboard_loads():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    res = client.get("/dashboard")
    assert res.status_code == 200

    data = res.json()
    assert "modules" in data
    assert "spelling" in data["modules"]


def test_dashboard_contract_shape():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    dashboard_res = client.get("/dashboard")
    assert dashboard_res.status_code == 200
    dashboard_data = _json_object(dashboard_res, "/dashboard")

    modules = dashboard_data.get("modules")
    assert isinstance(modules, dict), "/dashboard should include a modules object"

    for module_name in LEARNING_MODULES:
        if module_name in modules:
            _assert_learning_module_contract(module_name, modules[module_name])

    for module_name, module_data in modules.items():
        _assert_module_contract(module_name, module_data)

    insights_res = client.get("/dashboard/insights")
    assert insights_res.status_code == 200
    insights_data = _json_object(insights_res, "/dashboard/insights")
    streak = insights_data.get("streak")
    if streak is not None:
        assert isinstance(streak, dict), "/dashboard/insights streak should be an object"
        assert "current" in streak or "current_streak" in streak, (
            "/dashboard/insights streak should include current or current_streak"
        )

    engagement_res = client.get("/practice/engagement")
    assert engagement_res.status_code == 200
    engagement_data = _json_object(engagement_res, "/practice/engagement")
    assert "xp" in engagement_data, "/practice/engagement should include xp"
    assert "streak" in engagement_data, "/practice/engagement should include streak"

    improvement_res = client.get("/practice/progress/weekly-improvement")
    assert improvement_res.status_code == 200
    improvement_data = _json_object(improvement_res, "/practice/progress/weekly-improvement")
    assert "improvement" in improvement_data, (
        "/practice/progress/weekly-improvement should include improvement"
    )

    resume_res = client.get("/practice/resume")
    assert resume_res.status_code == 200
    try:
        resume_data = resume_res.json()
    except Exception as exc:
        raise AssertionError(f"/practice/resume did not return valid JSON: {exc}") from exc

    assert resume_data is None or isinstance(resume_data, dict), (
        "/practice/resume should return a JSON null or object"
    )


def test_dashboard_admin_unlocks_all_modules():
    client = APIClient()
    client.login(TEST_USERS["test_admin"]["email"], TEST_USERS["test_admin"]["password"])

    res = client.get("/dashboard")
    assert res.status_code == 200

    data = res.json()
    for module in data["modules"].values():
        assert module["unlocked"] == True


def test_no_token_dashboard():
    client = APIClient()
    res = client.get("/dashboard", token=None)

    assert res.status_code in [401, 403]
