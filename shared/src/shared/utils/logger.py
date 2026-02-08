"""Logging utilities with structured JSON logging support."""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add service name from environment
        service_name = os.getenv("SERVICE_NAME", "unknown")
        log_data["service"] = service_name

        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "merchant_id"):
            log_data["merchant_id"] = str(record.merchant_id)
        if hasattr(record, "payment_id"):
            log_data["payment_id"] = str(record.payment_id)

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """Structured logger wrapper."""

    def __init__(self, logger: logging.Logger):
        """Initialize structured logger."""
        self.logger = logger

    def _log_with_context(
        self,
        level: int,
        message: str,
        *args,
        request_id: Optional[str] = None,
        merchant_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        **kwargs,
    ):
        """Log with additional context."""
        extra = kwargs.get("extra", {})
        if request_id:
            extra["request_id"] = request_id
        if merchant_id:
            extra["merchant_id"] = merchant_id
        if payment_id:
            extra["payment_id"] = payment_id
        kwargs["extra"] = extra
        self.logger.log(level, message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)


def setup_logger(
    name: str,
    level: str = "INFO",
    format_string: Optional[str] = None,
    json_logs: Optional[bool] = None,
) -> logging.Logger:
    """
    Set up a logger with consistent formatting.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (ignored if json_logs=True)
        json_logs: Enable JSON logging (defaults to JSON_LOGS env var or False)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper()))

        # Check if JSON logging is enabled
        if json_logs is None:
            json_logs = os.getenv("JSON_LOGS", "false").lower() == "true"

        if json_logs:
            formatter = JSONFormatter()
        else:
            if format_string is None:
                format_string = (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(filename)s:%(lineno)d - %(message)s"
                )
            formatter = logging.Formatter(format_string)

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger  # pragma: no cover - simple return

