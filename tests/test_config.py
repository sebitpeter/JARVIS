from __future__ import annotations

import pytest

from app.config import Settings


def test_defaults_are_safe_and_key_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "ASSISTANT_NAME",
        "LOG_LEVEL",
        "REQUEST_TIMEOUT",
        "VOICE_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_environment()

    assert settings.assistant_name == "JARVIS"
    assert settings.gemini_model == "gemini-2.5-flash"
    assert not settings.has_api_key


def test_placeholder_is_not_treated_as_a_real_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "PASTE_YOUR_NEW_GEMINI_API_KEY_HERE")
    assert not Settings.from_environment().has_api_key


def test_rejects_invalid_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REQUEST_TIMEOUT", "0")
    with pytest.raises(ValueError, match="REQUEST_TIMEOUT"):
        Settings.from_environment()


def test_rejects_invalid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "LOUD")
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        Settings.from_environment()