"""Background tasks used by the Qt interface."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from app.gemini import GeminiAssistant, GeminiError
from app.voice import transcribe_once


class ChatWorker(QThread):
    result = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, assistant: GeminiAssistant, history: list[dict[str, str]]) -> None:
        super().__init__()
        self.assistant = assistant
        self.history = history

    def run(self) -> None:
        try:
            self.result.emit(self.assistant.reply(self.history))
        except GeminiError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("Something went wrong while preparing the reply. Please try again.")


class VoiceWorker(QThread):
    transcript = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, seconds: int) -> None:
        super().__init__()
        self.seconds = seconds

    def run(self) -> None:
        try:
            self.transcript.emit(transcribe_once(self.seconds))
        except RuntimeError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("Microphone input failed unexpectedly. Please try again.")


class SpeechWorker(QThread):
    failed = pyqtSignal(str)

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

    def run(self) -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.say(self.text)
            engine.runAndWait()
        except Exception:
            self.failed.emit(
                "Speech output is unavailable on this computer. Text chat still works."
            )