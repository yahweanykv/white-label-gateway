"""Unit tests for shared logger utilities."""

import json
import logging
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from shared.utils.logger import JSONFormatter, StructuredLogger, setup_logger


def test_json_formatter_format():
    """Test JSON formatter formatting."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    result = formatter.format(record)
    data = json.loads(result)

    assert data["level"] == "INFO"
    assert data["logger"] == "test"
    assert data["message"] == "Test message"
    assert data["module"] == "test"
    assert "timestamp" in data


def test_json_formatter_with_exception():
    """Test JSON formatter with exception."""
    formatter = JSONFormatter()
    try:
        raise ValueError("Test error")
    except ValueError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=sys.exc_info(),
        )

    result = formatter.format(record)
    data = json.loads(result)

    assert data["level"] == "ERROR"
    assert "exception" in data


def test_json_formatter_with_extra_fields():
    """Test JSON formatter with extra fields."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.extra_fields = {"key": "value"}

    result = formatter.format(record)
    data = json.loads(result)

    assert data["key"] == "value"


def test_json_formatter_with_context():
    """Test JSON formatter with request context."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req_123"
    record.merchant_id = "merchant_456"
    record.payment_id = "payment_789"

    result = formatter.format(record)
    data = json.loads(result)

    assert data["request_id"] == "req_123"
    assert data["merchant_id"] == "merchant_456"
    assert data["payment_id"] == "payment_789"


def test_structured_logger_debug():
    """Test structured logger debug method."""
    mock_logger = MagicMock(spec=logging.Logger)
    structured = StructuredLogger(mock_logger)

    structured.debug("Debug message")
    mock_logger.debug.assert_called_once_with("Debug message")


def test_structured_logger_info():
    """Test structured logger info method."""
    mock_logger = MagicMock(spec=logging.Logger)
    structured = StructuredLogger(mock_logger)

    structured.info("Info message")
    mock_logger.info.assert_called_once_with("Info message")


def test_structured_logger_warning():
    """Test structured logger warning method."""
    mock_logger = MagicMock(spec=logging.Logger)
    structured = StructuredLogger(mock_logger)

    structured.warning("Warning message")
    mock_logger.warning.assert_called_once_with("Warning message")


def test_structured_logger_error():
    """Test structured logger error method."""
    mock_logger = MagicMock(spec=logging.Logger)
    structured = StructuredLogger(mock_logger)

    structured.error("Error message")
    mock_logger.error.assert_called_once_with("Error message")


def test_structured_logger_critical():
    """Test structured logger critical method."""
    mock_logger = MagicMock(spec=logging.Logger)
    structured = StructuredLogger(mock_logger)

    structured.critical("Critical message")
    mock_logger.critical.assert_called_once_with("Critical message")


def test_structured_logger_with_context():
    """Test structured logger with context."""
    mock_logger = MagicMock(spec=logging.Logger)
    structured = StructuredLogger(mock_logger)

    structured._log_with_context(
        logging.INFO,
        "Message",
        request_id="req_123",
        merchant_id="merchant_456",
        payment_id="payment_789",
    )

    mock_logger.log.assert_called_once()
    call_kwargs = mock_logger.log.call_args[1]
    assert call_kwargs["extra"]["request_id"] == "req_123"
    assert call_kwargs["extra"]["merchant_id"] == "merchant_456"
    assert call_kwargs["extra"]["payment_id"] == "payment_789"


def test_setup_logger_default():
    """Test setting up logger with defaults."""
    logger = setup_logger("test_logger")
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_setup_logger_custom_level():
    """Test setting up logger with custom level."""
    logger = setup_logger("test_logger", level="DEBUG")
    assert logger.level == logging.DEBUG


def test_setup_logger_json_logs(monkeypatch):
    """Test setting up logger with JSON logging."""
    monkeypatch.setenv("JSON_LOGS", "true")
    logger = setup_logger("test_logger")
    assert len(logger.handlers) > 0
    # Check if formatter is JSONFormatter
    handler = logger.handlers[0]
    assert isinstance(handler.formatter, JSONFormatter)


def test_setup_logger_text_logs(monkeypatch):
    """Test setting up logger with text logging."""
    monkeypatch.setenv("JSON_LOGS", "false")
    logger = setup_logger("test_logger")
    assert len(logger.handlers) > 0
    # Check if formatter is not JSONFormatter
    handler = logger.handlers[0]
    assert not isinstance(handler.formatter, JSONFormatter)


def test_setup_logger_custom_format():
    """Test setting up logger with custom format."""
    custom_format = "%(message)s"
    logger = setup_logger("test_logger", format_string=custom_format, json_logs=False)
    handler = logger.handlers[0]
    assert handler.formatter._fmt == custom_format


def test_setup_logger_idempotent():
    """Test that setup_logger is idempotent."""
    logger1 = setup_logger("test_logger")
    handler_count1 = len(logger1.handlers)

    logger2 = setup_logger("test_logger")
    handler_count2 = len(logger2.handlers)

    assert logger1 is logger2
    assert handler_count1 == handler_count2
