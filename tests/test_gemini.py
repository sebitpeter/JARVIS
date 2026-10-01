from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from app.gemini import GeminiAssistant, GeminiError


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_reply_posts_conversation_and_extracts_text() -> None:
    history = [{"role": "user", "text": "Hello"}]
    response_body = {
        "candidates": [{"content": {"parts": [{"text": "Hello there."}]}}]
    }
    with patch("app.gemini.urlopen", return_value=FakeResponse(response_body)) as mocked:
        answer = GeminiAssistant("test-key", "gemini-test").reply(history)

    assert answer == "Hello there."
    request = mocked.call_args.args[0]
    assert request.get_method() == "POST"
    assert request.get_header("X-goog-api-key") == "test-key"
    sent = json.loads(request.data.decode())
    assert sent["contents"][0]["parts"][0]["text"] == "Hello"


def test_reply_requires_a_user_message_at_the_end() -> None:
    assistant = GeminiAssistant("test-key", "gemini-test")
    with pytest.raises(ValueError, match="end with a user message"):
        assistant.reply([{"role": "model", "text": "Hello"}])


def test_invalid_key_error_does_not_expose_provider_detail() -> None:
    error_body = b'{"error":{"message":"API key abc-secret is invalid"}}'
    http_error = HTTPError(
        "https://example.invalid",
        403,
        "Forbidden",
        hdrs=None,
        fp=BytesIO(error_body),
    )
    with patch("app.gemini.urlopen", side_effect=http_error):
        with pytest.raises(GeminiError, match="Gemini rejected the API key") as exc:
            GeminiAssistant("test-key", "gemini-test").reply(
                [{"role": "user", "text": "Hello"}]
            )
    assert "abc-secret" not in str(exc.value)