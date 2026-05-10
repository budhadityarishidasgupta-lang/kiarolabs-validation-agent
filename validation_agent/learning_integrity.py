import re


class ValidationWarning(Exception):
    pass


def _normalized_text(value) -> str:
    return str(value or "").strip()


def infer_module(name: str) -> str:
    lowered = (name or "").lower()
    if "spelling" in lowered:
        return "spelling"
    if "words" in lowered or "synonym" in lowered:
        return "words"
    if "comprehension" in lowered:
        return "comprehension"
    if "math" in lowered:
        return "math"
    if "dashboard" in lowered:
        return "dashboard"
    if "auth" in lowered or "login" in lowered or "password" in lowered:
        return "platform"
    return "general"


def infer_validator(name: str, detail: str = "") -> str:
    lowered = f"{name} {detail}".lower()
    if "answer_integrity" in lowered or "answer in options" in lowered or "correct_answer was not present" in lowered:
        return "answer_in_options"
    if "duplicate" in lowered:
        return "duplicate_options"
    if "blank option" in lowered or "empty option" in lowered:
        return "empty_options"
    if "cooldown" in lowered or "immediate_repeat" in lowered or "repeat violation" in lowered:
        return "question_cooldown"
    if "leak" in lowered or "pre-submit" in lowered:
        return "answer_leakage"
    if "progression" in lowered or "position" in lowered or "advance" in lowered:
        return "session_progression"
    if "review distribution" in lowered or "review domination" in lowered:
        return "review_distribution"
    return "general_validation"


def infer_severity(name: str, status: str, detail: str = "") -> str:
    validator = infer_validator(name, detail)
    if status == "warned":
        return "MEDIUM"
    if validator in {"answer_in_options", "answer_leakage"}:
        return "CRITICAL"
    if validator in {"duplicate_options", "empty_options", "question_cooldown", "session_progression"}:
        return "HIGH"
    return "MEDIUM"


def describe_result(name: str, status: str, detail: str = "") -> dict:
    return {
        "module": infer_module(name),
        "validator": infer_validator(name, detail),
        "severity": infer_severity(name, status, detail),
    }


def assert_no_answer_leakage(item: dict, *, context: str):
    example_sentence = item.get("example_sentence")
    assert example_sentence in {None, "", []}, (
        f"{context}: pre-submit payload leaked example_sentence: {item}"
    )

    forbidden_answer_fields = (
        "correct_answer",
        "correct_word",
        "answer",
    )
    for field in forbidden_answer_fields:
        if field in item:
            value = item.get(field)
            assert value in {None, ""}, (
                f"{context}: pre-submit payload leaked {field}: {item}"
            )


def assert_options_integrity(*, item_id, headword, options, context: str):
    assert isinstance(options, list), f"{context}: options must be a list for item_id={item_id}: {options!r}"
    assert len(options) >= 4, f"{context}: expected at least 4 options for item_id={item_id}: {options!r}"

    seen = set()
    normalized_headword = _normalized_text(headword).lower()
    for option in options:
        assert isinstance(option, str), f"{context}: option must be a string for item_id={item_id}: {options!r}"
        cleaned = option.strip()
        lowered = cleaned.lower()
        assert cleaned, f"{context}: blank option returned for item_id={item_id}: {options!r}"
        assert not re.fullmatch(r"\d+", cleaned), (
            f"{context}: numeric-only junk option returned for item_id={item_id}: {options!r}"
        )
        assert lowered not in seen, (
            f"{context}: duplicate option returned for item_id={item_id}: {options!r}"
        )
        if normalized_headword:
            assert lowered != normalized_headword, (
                f"{context}: option should not equal headword for item_id={item_id}: "
                f"headword={headword!r}, options={options!r}"
            )
        seen.add(lowered)


def assert_answer_in_options(*, item_id, headword, options, correct_answer, context: str):
    normalized_options = {_normalized_text(option).lower() for option in options}
    normalized_correct = _normalized_text(correct_answer).lower()
    assert normalized_correct, (
        f"{context}: missing correct answer for item_id={item_id}, headword={headword!r}, options={options!r}"
    )
    assert normalized_correct in normalized_options, (
        f"{context}: correct answer missing from displayed options for item_id={item_id}, "
        f"headword={headword!r}, options={options!r}, correct_answer={correct_answer!r}"
    )


def assert_progression_advances(previous: dict, current: dict, *, context: str):
    previous_state = previous.get("session_state") if isinstance(previous, dict) else None
    current_state = current.get("session_state") if isinstance(current, dict) else None
    if not isinstance(previous_state, dict) or not isinstance(current_state, dict):
        return

    previous_position = previous_state.get("question_position")
    current_position = current_state.get("question_position")
    if previous_position is None or current_position is None:
        return

    assert int(current_position) > int(previous_position), (
        f"{context}: session progression pointer did not advance: "
        f"previous_position={previous_position}, current_position={current_position}, "
        f"previous={previous}, current={current}"
    )


def warn_if_review_distribution_excessive(observed_items: list[dict], *, context: str, threshold: float = 0.6):
    if not observed_items:
        return

    review_count = 0
    review_signal_count = 0
    for item in observed_items:
        if not isinstance(item, dict):
            continue
        is_review = bool(item.get("is_review") or (item.get("session_state") or {}).get("is_review"))
        if is_review:
            review_count += 1
        if any(key in item for key in ("is_review", "review_reason", "encouragement_message", "session_state")):
            review_signal_count += 1

    if review_signal_count == 0:
        return

    ratio = review_count / max(len(observed_items), 1)
    if ratio > threshold:
        raise ValidationWarning(
            f"{context}: review distribution warning - {review_count}/{len(observed_items)} "
            f"questions were review items ({ratio:.0%})."
        )
