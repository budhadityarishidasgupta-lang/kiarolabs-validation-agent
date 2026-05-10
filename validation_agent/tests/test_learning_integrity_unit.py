from validation_agent.learning_integrity import assert_no_answer_leakage


def test_assert_no_answer_leakage_accepts_empty_list_example_sentence():
    assert_no_answer_leakage({"example_sentence": []}, context="unit")


def test_assert_no_answer_leakage_rejects_populated_example_sentence():
    try:
        assert_no_answer_leakage({"example_sentence": "Leaked sentence"}, context="unit")
    except AssertionError:
        return

    raise AssertionError("Expected populated example_sentence to fail leakage validation.")
