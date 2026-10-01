"""Small Gemini REST client using only Python's standard library."""

from __future__ import annotations

import json
import logging
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiError(RuntimeError):
    """A safe-to-show error returned by the Gemini client."""


class GeminiAssistant:
    def __init__(self, api_key: str, model: str, timeout: int = 45) -> None:
        if not api_key.strip():
            raise ValueError("A Gemini API key is required.")
        self._api_key = api_key.strip()
        self.model = model.strip()
        self.timeout = timeout

    def reply(self, history: Iterable[dict[str, str]]) -> str:
        contents: list[dict[str, object]] = []
        for item in history:
            role = item.get("role")
            text = item.get("text", "").strip()
            if role in {"user", "model"} and text:
                contents.append({"role": role, "parts": [{"text": text}]})
        if not contents or contents[-1]["role"] != "user":
            raise ValueError("Conversation history must end with a user message.")

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are JARVIS, a capable, clear, and trustworthy personal "
                            "desktop assistant. Be useful and concise. Do not claim to "
                            "have performed actions outside this chat."
                        )
                    }
                ]
            },
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
        }
        model_path = quote(self.model, safe="-_.")
        request = Request(
            f"{API_ROOT}/{model_path}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": self._api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            message = self._read_provider_error(exc)
            logger.warning("Gemini request failed with HTTP %s.", exc.code)
            raise GeminiError(message) from None
        except URLError as exc:
            logger.warning("Gemini connection failed: %s", exc.reason)
            raise GeminiError(
                "Could not reach Gemini. Check your internet connection and try again."
            ) from None
        except TimeoutError:
            raise GeminiError("Gemini took too long to respond. Please try again.") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise GeminiError("Gemini returned an unreadable response. Please try again.") from None
        except OSError:
            raise GeminiError("A network error interrupted the Gemini request.") from None

        try:
            candidates = response_data.get("candidates", [])
            parts = candidates[0]["content"]["parts"]
            answer = "\n".join(
                part["text"].strip()
                for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ).strip()
        except (IndexError, KeyError, TypeError, AttributeError):
            answer = ""
        if not answer:
            raise GeminiError(
                "Gemini did not return a text answer. Try rephrasing your message."
            )
        return answer

    @staticmethod
    def _read_provider_error(error: HTTPError) -> str:
        try:
            data = json.loads(error.read().decode("utf-8"))
            provider_message = data.get("error", {}).get("message", "")
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            provider_message = ""

        message = str(provider_message).lower()
        if error.code in {401, 403} or "api key" in message or "api_key" in message:
            return (
                "Gemini rejected the API key. Check that your key is valid and enabled "
                "for the Gemini API."
            )
        if error.code == 429:
            return "Gemini's usage limit was reached. Wait a little, then try again."
        if error.code == 404:
            return "The configured Gemini model was not found. Update GEMINI_MODEL in .env."
        if error.code >= 500:
            return "Gemini is temporarily unavailable. Please try again shortly."
        return "Gemini could not process that request. Check the model and API settings."