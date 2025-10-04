"""In-memory log buffer used to surface backend logs to the web UI."""

from __future__ import annotations

import logging
import threading
import traceback
from collections import deque
from typing import Deque, Dict, List, Optional


class LogBufferHandler(logging.Handler):
    """Logging handler that stores recent log records for later retrieval."""

    def __init__(self, capacity: int = 500, level: int = logging.INFO) -> None:
        super().__init__(level=level)
        self.capacity = capacity
        self._lock = threading.Lock()
        self._records: Deque[Dict[str, object]] = deque(maxlen=capacity)
        self._next_id = 1
        self._fallback_formatter = logging.Formatter("%(message)s")

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401 - logging interface
        try:
            # Ensure the formatter can display exception information.
            if record.exc_info and not getattr(record, "exc_text", None):
                record.exc_text = ''.join(traceback.format_exception(*record.exc_info))

            formatter = self.formatter or self._fallback_formatter
            formatted = formatter.format(record)

            entry = {
                "id": self._next_sequence(),
                "level": record.levelname,
                "logger": record.name,
                "created": record.created,
                "message": record.getMessage(),
                "formatted": formatted,
                "module": record.module,
                "func": record.funcName,
                "line": record.lineno,
            }

            if record.exc_info and record.exc_text:
                entry["exception"] = record.exc_text

        except Exception:  # pragma: no cover - safeguard for logging failures
            self.handleError(record)
            return

        with self._lock:
            self._records.append(entry)

    def get_entries(self, since: int = 0, limit: Optional[int] = None) -> List[Dict[str, object]]:
        """Return records with an id greater than *since* in ascending order."""

        with self._lock:
            records = list(self._records)

        if since:
            records = [item for item in records if int(item["id"]) > since]

        if limit is not None and limit > 0:
            records = records[-limit:]

        return records

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def _next_sequence(self) -> int:
        with self._lock:
            current = self._next_id
            self._next_id += 1
            return current


log_buffer_handler = LogBufferHandler()


def get_logs(since: int = 0, limit: Optional[int] = None) -> List[Dict[str, object]]:
    """Convenience wrapper to query the shared log buffer."""

    return log_buffer_handler.get_entries(since=since, limit=limit)


__all__ = ["LogBufferHandler", "log_buffer_handler", "get_logs"]
