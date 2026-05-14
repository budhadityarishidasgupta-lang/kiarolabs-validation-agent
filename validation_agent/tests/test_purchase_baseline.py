from validation_agent.skills.checks import load_json


def test_purchase_baseline_placeholder_requires_manual_check(tmp_path):
    baseline = tmp_path / "purchase_link_baseline.json"
    baseline.write_text(
        '{"status":"NEEDS_MANUAL_CHECK","purchase_urls":[]}',
        encoding="utf-8",
    )
    payload = load_json(baseline)
    assert payload["status"] == "NEEDS_MANUAL_CHECK"
    assert payload["purchase_urls"] == []


def test_purchase_baseline_parses_urls(tmp_path):
    baseline = tmp_path / "purchase_link_baseline.json"
    baseline.write_text(
        '{"status":"APPROVED","purchase_urls":["https://gumroad.com/l/example"]}',
        encoding="utf-8",
    )
    payload = load_json(baseline)
    assert "https://gumroad.com/l/example" in payload["purchase_urls"]
