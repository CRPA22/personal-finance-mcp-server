"""Structured logging configuration."""

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        # Extra fields from record
        extra = {k: v for k, v in record.__dict__.items() if k not in logging.LogRecord.__dict__}
        if extra:
            log_obj["extra"] = {k: str(v) for k, v in extra.items()}
        return json.dumps(log_obj, default=str)


def configure_logging(
    log_level: str | None = None,
    json_format: bool | None = None,
) -> None:
    """Configure application logging.

    Args:
        log_level: DEBUG, INFO, WARNING, ERROR. Default from settings.
        json_format: True for JSON output (production), False for human-readable.
    """
    level = getattr(logging, (log_level or settings.log_level).upper(), logging.INFO)
    use_json = json_format if json_format is not None else (settings.log_level.upper() != "DEBUG")

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root.addHandler(handler)

    # Reduce noise from third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name."""
    return logging.getLogger(name)
