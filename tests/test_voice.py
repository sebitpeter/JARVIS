from app.voice import is_wake_word_detected


def test_wake_word_score_at_threshold_activates() -> None:
    assert is_wake_word_detected({"hey_jarvis": 0.5})


def test_wake_word_score_below_threshold_does_not_activate() -> None:
    assert not is_wake_word_detected({"hey_jarvis": 0.49})


def test_wake_word_handles_array_like_score_values() -> None:
    assert is_wake_word_detected({"hey_jarvis": [0.12, 0.68, 0.31]})


def test_wake_word_ignores_invalid_scores() -> None:
    assert not is_wake_word_detected({"hey_jarvis": "unknown"})