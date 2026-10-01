"""Launch the JARVIS desktop assistant."""

from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

from app.config import Settings
from app.ui.window import AssistantWindow


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    load_dotenv()
    try:
        settings = Settings.from_environment()
    except (ValueError, OSError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    configure_logging(settings.log_level)
    application = QApplication(sys.argv)
    application.setApplicationName(settings.assistant_name)
    window = AssistantWindow(settings)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())