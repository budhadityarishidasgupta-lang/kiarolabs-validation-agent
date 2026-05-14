from validation_agent.skills.checks import detect_unlocked_query_param_trust


def test_detect_unlocked_true_query_spoofing():
    text = """
    const unlocked = params.get('unlocked') === 'true';
    const fullAccess = unlocked;
    """
    assert detect_unlocked_query_param_trust(text) is True


def test_ignore_when_unlocked_not_authoritative():
    text = """
    const unlocked = params.get('unlocked') === 'true';
    const label = unlocked ? 'debug' : 'normal';
    """
    assert detect_unlocked_query_param_trust(text) is False
