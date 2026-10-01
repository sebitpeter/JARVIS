"""Main JARVIS desktop window."""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import Settings
from app.gemini import GeminiAssistant
from app.ui.workers import ChatWorker, SpeechWorker, VoiceWorker
from app.ui.wake_worker import WakeWordWorker

logger = logging.getLogger(__name__)


class AssistantWindow(QMainWindow):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.conversation: list[dict[str, str]] = []
        self.chat_worker: ChatWorker | None = None
        self.voice_worker: VoiceWorker | None = None
        self.speech_worker: SpeechWorker | None = None
        self.wake_worker: WakeWordWorker | None = None
        self._wake_command_pending = False
        self._wake_failed = False
        self._close_requested = False

        self.setWindowTitle(f"{settings.assistant_name} — Desktop Assistant")
        self.resize(780, 620)
        self.setMinimumSize(560, 420)
        self._build_ui()
        self._set_theme()
        self._append_message(
            settings.assistant_name,
            "Ready when you are. Ask me anything, or use the microphone button to dictate.",
        )
        if not settings.has_api_key:
            self.status_label.setText("Setup needed: add a Gemini API key to .env, then restart.")

    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        heading = QLabel(self.settings.assistant_name)
        heading.setObjectName("heading")
        subtitle = QLabel("YOUR PERSONAL DESKTOP ASSISTANT")
        subtitle.setObjectName("subtitle")
        outer.addWidget(heading)
        outer.addWidget(subtitle)

        self.chat_view = QPlainTextEdit()
        self.chat_view.setObjectName("chat")
        self.chat_view.setReadOnly(True)
        self.chat_view.setPlaceholderText("Your conversation will appear here.")
        outer.addWidget(self.chat_view, 1)

        controls = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Message JARVIS…")
        self.input_field.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_message)
        self.mic_button = QPushButton("🎙  Dictate")
        self.mic_button.setToolTip(
            f"Record up to {self.settings.voice_seconds} seconds and transcribe it online."
        )
        self.mic_button.clicked.connect(self._start_manual_voice_input)
        controls.addWidget(self.input_field, 1)
        controls.addWidget(self.mic_button)
        controls.addWidget(self.send_button)
        outer.addLayout(controls)

        footer = QHBoxLayout()
        self.status_label = QLabel("Text chat is ready.")
        self.status_label.setObjectName("status")
        self.read_aloud = QCheckBox("Read replies aloud")
        self.read_aloud.setChecked(False)
        self.wake_toggle = QCheckBox("Wake word: off")
        self.wake_toggle.setToolTip(
            "When enabled, the microphone stays active for local 'Hey JARVIS' detection. "
            "Toggle off to stop listening."
        )
        self.wake_toggle.toggled.connect(self._toggle_wake_word)
        footer.addWidget(self.status_label, 1)
        footer.addWidget(self.read_aloud)
        footer.addWidget(self.wake_toggle)
        outer.addLayout(footer)

        self.setCentralWidget(central)

    def _set_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #10141c; color: #e7edf7; }
            QLabel#heading { color: #f2f6ff; font-size: 28px; font-weight: 700; }
            QLabel#subtitle { color: #8190a8; font-size: 10px; letter-spacing: 2px; }
            QPlainTextEdit#chat {
                background: #171d28; border: 1px solid #273244; border-radius: 12px;
                padding: 14px; color: #e7edf7; font-size: 14px;
                selection-background-color: #335d95;
            }
            QLineEdit {
                background: #171d28; border: 1px solid #344157; border-radius: 9px;
                padding: 11px 13px; color: #f2f6ff; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #70a7ff; }
            QPushButton {
                background: #222c3b; border: 1px solid #36445a; border-radius: 9px;
                padding: 10px 14px; color: #e7edf7; font-weight: 600;
            }
            QPushButton:hover { background: #2b394d; }
            QPushButton:disabled { color: #778398; background: #1a202b; }
            QPushButton#sendButton { background: #3979d6; border-color: #3979d6; }
            QPushButton#sendButton:hover { background: #4a8ae7; }
            QLabel#status { color: #9eacc0; font-size: 12px; }
            QCheckBox { color: #b8c4d6; spacing: 7px; font-size: 12px; }
            QCheckBox::indicator { width: 15px; height: 15px; }
            """
        )

    def _append_message(self, speaker: str, text: str) -> None:
        if self.chat_view.toPlainText():
            self.chat_view.appendPlainText("")
        self.chat_view.appendPlainText(f"{speaker}\n{text}")
        cursor = self.chat_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chat_view.setTextCursor(cursor)

    def send_message(self) -> None:
        text = self.input_field.text().strip()
        if not text or (self.chat_worker is not None and self.chat_worker.isRunning()):
            return
        if not self.settings.has_api_key:
            self.status_label.setText("Add your Gemini API key to .env, then restart JARVIS.")
            self._append_message(
                self.settings.assistant_name,
                "I need a Gemini API key before I can answer. Follow the setup steps in README.md.",
            )
            return

        self.input_field.clear()
        self.conversation.append({"role": "user", "text": text})
        self._append_message("You", text)
        history = self.conversation[-20:]
        if history and history[0]["role"] == "model":
            history = history[1:]
        self.chat_worker = ChatWorker(
            GeminiAssistant(
                self.settings.gemini_api_key,
                self.settings.gemini_model,
                self.settings.request_timeout,
            ),
            history,
        )
        self.chat_worker.result.connect(self._on_reply)
        self.chat_worker.failed.connect(self._on_chat_error)
        self.chat_worker.finished.connect(self._on_chat_finished)
        self.send_button.setEnabled(False)
        self.mic_button.setEnabled(False)
        self.status_label.setText("Thinking…")
        self.chat_worker.start()

    def _on_reply(self, answer: str) -> None:
        self.conversation.append({"role": "model", "text": answer})
        self._append_message(self.settings.assistant_name, answer)
        self.status_label.setText("Reply received.")
        if self.read_aloud.isChecked():
            self._speak(answer)

    def _on_chat_error(self, message: str) -> None:
        logger.info("Chat request did not complete.")
        self._append_message(self.settings.assistant_name, message)
        self.status_label.setText("The reply could not be completed.")

    def _on_chat_finished(self) -> None:
        self.chat_worker = None
        if self._close_requested:
            self._close_when_workers_finish()
            return
        if self.wake_toggle.isChecked():
            if self.speech_worker is None or not self.speech_worker.isRunning():
                self._start_wake_listener()
        else:
            self._refresh_controls()
            self.input_field.setFocus()

    def _start_manual_voice_input(self) -> None:
        self.start_voice_input()

    def start_voice_input(self, *, from_wake_word: bool = False) -> None:
        if self.voice_worker is not None and self.voice_worker.isRunning():
            return
        if self.chat_worker is not None and self.chat_worker.isRunning():
            return
        self._wake_command_pending = from_wake_word
        self.mic_button.setEnabled(False)
        self.send_button.setEnabled(False)
        self.input_field.setEnabled(False)
        self.status_label.setText(
            "Wake word heard. Listening for your command…"
            if from_wake_word
            else f"Listening for up to {self.settings.voice_seconds} seconds…"
        )
        self.voice_worker = VoiceWorker(self.settings.voice_seconds)
        self.voice_worker.transcript.connect(self._on_transcript)
        self.voice_worker.failed.connect(self._on_voice_error)
        self.voice_worker.finished.connect(self._on_voice_finished)
        self.voice_worker.start()

    def _on_transcript(self, text: str) -> None:
        self.input_field.setText(text)
        if self._wake_command_pending:
            self._wake_command_pending = False
            self.status_label.setText("Command transcribed. Sending it to JARVIS…")
            self.send_message()
        else:
            self.status_label.setText("Transcription ready. Press Send to ask JARVIS.")

    def _on_voice_error(self, message: str) -> None:
        self._wake_command_pending = False
        self.status_label.setText(message)

    def _on_voice_finished(self) -> None:
        self.mic_button.setEnabled(True)
        self.voice_worker = None
        if self._close_requested:
            self._close_when_workers_finish()
            return
        if self.wake_toggle.isChecked():
            if self.chat_worker is None or not self.chat_worker.isRunning():
                self._start_wake_listener()
        else:
            self._refresh_controls()

    def _toggle_wake_word(self, enabled: bool) -> None:
        self.wake_toggle.setText("Wake word: on" if enabled else "Wake word: off")
        if enabled:
            self._wake_failed = False
            self._start_wake_listener()
            return
        self._wake_command_pending = False
        if self.wake_worker is not None and self.wake_worker.isRunning():
            self.wake_worker.stop_listening()
            self.status_label.setText("Turning wake-word listening off…")
        else:
            self.status_label.setText("Wake-word listening is off.")
            self._refresh_controls()

    def _start_wake_listener(self) -> None:
        if (
            self._close_requested
            or not self.wake_toggle.isChecked()
            or (self.wake_worker is not None and self.wake_worker.isRunning())
            or (self.voice_worker is not None and self.voice_worker.isRunning())
            or (self.chat_worker is not None and self.chat_worker.isRunning())
        ):
            return
        self._wake_failed = False
        self.status_label.setText(
            "Starting local “Hey JARVIS” detection. The first run may download its model."
        )
        self._refresh_controls(listening_for_wake_word=True)
        self.wake_worker = WakeWordWorker()
        self.wake_worker.failed.connect(self._on_wake_error)
        self.wake_worker.finished.connect(self._on_wake_finished)
        self.wake_worker.start()

    def _on_wake_error(self, message: str) -> None:
        self._wake_failed = True
        self.status_label.setText(message)
        self.wake_toggle.blockSignals(True)
        self.wake_toggle.setChecked(False)
        self.wake_toggle.setText("Wake word: off")
        self.wake_toggle.blockSignals(False)

    def _on_wake_finished(self) -> None:
        worker = self.wake_worker
        detected = worker.detected if worker is not None else False
        self.wake_worker = None
        if self._close_requested:
            self._close_when_workers_finish()
            return
        if detected and self.wake_toggle.isChecked():
            self.start_voice_input(from_wake_word=True)
        elif self.wake_toggle.isChecked():
            # A device/model failure already switched the toggle off.
            self._start_wake_listener()
        else:
            if not self._wake_failed:
                self.status_label.setText("Wake-word listening is off.")
            self._wake_failed = False
            self._refresh_controls()

    def _refresh_controls(self, *, listening_for_wake_word: bool = False) -> None:
        chat_busy = self.chat_worker is not None and self.chat_worker.isRunning()
        voice_busy = self.voice_worker is not None and self.voice_worker.isRunning()
        self.input_field.setEnabled(not chat_busy and not voice_busy and not listening_for_wake_word)
        self.send_button.setEnabled(not chat_busy and not voice_busy and not listening_for_wake_word)
        self.mic_button.setEnabled(not chat_busy and not voice_busy and not listening_for_wake_word)

    def _speak(self, text: str) -> None:
        if self.speech_worker is not None and self.speech_worker.isRunning():
            return
        self.speech_worker = SpeechWorker(text)
        self.speech_worker.failed.connect(self.status_label.setText)
        self.speech_worker.finished.connect(self._on_speech_finished)
        self.speech_worker.start()

    def _on_speech_finished(self) -> None:
        self.speech_worker = None
        if (
            not self._close_requested
            and self.wake_toggle.isChecked()
            and (self.chat_worker is None or not self.chat_worker.isRunning())
            and (self.voice_worker is None or not self.voice_worker.isRunning())
        ):
            self._start_wake_listener()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt event API
        self._close_requested = True
        if self.wake_worker is not None and self.wake_worker.isRunning():
            self.wake_worker.stop_listening()
        workers = (self.chat_worker, self.voice_worker, self.speech_worker, self.wake_worker)
        running_workers = [
            worker for worker in workers if worker is not None and worker.isRunning()
        ]
        if running_workers:
            event.ignore()
            self.status_label.setText("Closing after the active operation finishes…")
            self.setEnabled(False)
            for worker in running_workers:
                worker.finished.connect(self._close_when_workers_finish)
            return
        event.accept()

    def _close_when_workers_finish(self) -> None:
        if self._close_requested and not any(
            worker is not None and worker.isRunning()
            for worker in (
                self.chat_worker,
                self.voice_worker,
                self.speech_worker,
                self.wake_worker,
            )
        ):
            self.close()