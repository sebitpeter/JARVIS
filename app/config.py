"""Environment-based application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _positive_int(name: str, default: int, *, maximum: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a whole number.") from exc
    if value < 1 or value > maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}.")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    assistant_name: str
    log_level: str
    request_timeout: int
    voice_seconds: int

    @property
    def has_api_key(self) -> bool:
        return bool(self.gemini_api_key.strip()) and (
            self.gemini_api_key.strip() != "PASTE_YOUR_NEW_GEMINI_API_KEY_HERE"
        )

    @classmethod
    def from_environment(cls) -> "Settings":
        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL.")

        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        if not model or any(char.isspace() for char in model):
            raise ValueError("GEMINI_MODEL must be a non-empty model name without spaces.")

        assistant_name = os.getenv("ASSISTANT_NAME", "JARVIS").strip() or "JARVIS"
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=model,
            assistant_name=assistant_name[:40],
            log_level=log_level,
            request_timeout=_positive_int("REQUEST_TIMEOUT", 45, maximum=180),
            voice_seconds=_positive_int("VOICE_SECONDS", 6, maximum=30),
        )