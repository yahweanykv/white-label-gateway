"""Unit tests for gateway config."""

import os
import pytest

from gateway.config import Settings


def test_settings_defaults(monkeypatch):
    """Test default settings values."""
    # Clear environment variables that might affect defaults
    monkeypatch.delenv("GATEWAY_LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("GATEWAY_HOST", raising=False)
    monkeypatch.delenv("GATEWAY_PORT", raising=False)
    monkeypatch.delenv("GATEWAY_ENV", raising=False)

    settings = Settings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.env == "development"
    assert settings.log_level == "INFO"


def test_cors_origins_list_comma_separated():
    """Test CORS origins parsing from comma-separated string."""
    settings = Settings(cors_origins="http://localhost:3000,http://localhost:8080")
    origins = settings.cors_origins_list
    assert len(origins) == 2
    assert "http://localhost:3000" in origins
    assert "http://localhost:8080" in origins


def test_cors_origins_list_json():
    """Test CORS origins parsing from JSON list."""
    settings = Settings(cors_origins='["http://localhost:3000", "http://localhost:8080"]')
    origins = settings.cors_origins_list
    assert len(origins) == 2
    assert "http://localhost:3000" in origins
    assert "http://localhost:8080" in origins


def test_cors_origins_list_empty():
    """Test CORS origins parsing with empty string."""
    settings = Settings(cors_origins="")
    origins = settings.cors_origins_list
    assert origins == []


def test_cors_origins_list_invalid_json():
    """Test CORS origins parsing with invalid JSON falls back to comma-separated."""
    settings = Settings(cors_origins="[invalid json")
    origins = settings.cors_origins_list
    # Should fall back to comma-separated parsing
    assert isinstance(origins, list)


def test_cors_origins_list_with_spaces():
    """Test CORS origins parsing with spaces."""
    settings = Settings(cors_origins=" http://localhost:3000 , http://localhost:8080 ")
    origins = settings.cors_origins_list
    assert len(origins) == 2
    assert "http://localhost:3000" in origins
    assert "http://localhost:8080" in origins


def test_settings_from_env(monkeypatch):
    """Test settings loading from environment variables."""
    monkeypatch.setenv("GATEWAY_HOST", "127.0.0.1")
    monkeypatch.setenv("GATEWAY_PORT", "9000")
    monkeypatch.setenv("GATEWAY_ENV", "production")

    settings = Settings()
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.env == "production"
