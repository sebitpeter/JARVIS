"""Background wake-word listener."""

from __future__ import annotations

from threading import Event

from PyQt6.QtCore import QThread, pyqtSignal

from app.voice import wait_for_jarvis_wake_word


class WakeWordWorker(QThread):
    failed = pyqtSignal(str)

    def __init__(self, threshold: float = 0.5) -> None:
        super().__init__()
        self.stop_event = Event()
        self.threshold = threshold
        self.detected = False

    def stop_listening(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        try:
            self.detected = wait_for_jarvis_wake_word(
                self.stop_event, threshold=self.threshold
            )
        except RuntimeError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("Wake-word detection stopped after an unexpected error.")