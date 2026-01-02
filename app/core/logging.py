import logging
import sys
from typing import Any, Dict

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, self.datefmt),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return str(log_record)


def setup_logging() -> None:
    """
    Configure application-wide logging using env-based log level.
    """

    log_level = settings.LOG_LEVEL.upper()

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(JsonFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
