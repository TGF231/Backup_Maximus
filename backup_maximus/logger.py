"""Log diário em arquivo: logs/backup_AAAA-MM-DD.log, UTF-8."""

from __future__ import annotations

import os
import threading
from datetime import datetime

_lock = threading.Lock()
_log_dir = ""


def init(app_dir: str) -> None:
    global _log_dir
    _log_dir = os.path.join(app_dir, "logs")
    os.makedirs(_log_dir, exist_ok=True)


def current_path() -> str:
    return os.path.join(_log_dir, f"backup_{datetime.now():%Y-%m-%d}.log")


def _write(level: str, msg: str) -> None:
    if not _log_dir:
        return
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [{level:<5}] {msg}\r\n"
    with _lock:
        try:
            with open(current_path(), "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            pass  # log indisponível nunca deve derrubar o backup


def info(msg: str) -> None:
    _write("INFO", msg)


def warn(msg: str) -> None:
    _write("WARN", msg)


def error(msg: str) -> None:
    _write("ERROR", msg)
