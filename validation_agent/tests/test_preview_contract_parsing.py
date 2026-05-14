from validation_agent.skills.checks import load_simple_yaml


def test_preview_contract_parsing(tmp_path):
    config = tmp_path / "preview_contract.yml"
    config.write_text(
        "preview_question_limit: 5\naccess_states:\n  - full\n  - preview\n  - locked\n",
        encoding="utf-8",
    )
    parsed = load_simple_yaml(config)
    assert parsed["preview_question_limit"] == 5
    assert parsed["access_states"] == ["full", "preview", "locked"]
