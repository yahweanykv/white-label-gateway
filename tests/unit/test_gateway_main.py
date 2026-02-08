"""Unit tests for gateway main."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from gateway.main import app, custom_openapi, lifespan, root, metrics, signal_handler


class TestGatewayMain:
    """Tests for gateway main module."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "White-Label Payment Gateway API"
        assert data["version"] == "1.0.0"
        assert "docs" in data
        assert "health" in data
        assert "metrics" in data

    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        # Check that metrics content contains some expected strings
        content = response.text
        assert len(content) > 0

    def test_custom_openapi(self):
        """Test custom OpenAPI schema generation."""
        # Clear cached schema
        app.openapi_schema = None

        schema = custom_openapi()
        assert schema is not None
        assert "info" in schema
        assert schema["info"]["title"] == "White-Label Payment Gateway API"
        assert "x-logo" in schema["info"]
        assert "contact" in schema["info"]
        assert "license" in schema["info"]

        # Test caching
        schema2 = custom_openapi()
        assert schema2 is schema

    @pytest.mark.asyncio
    async def test_lifespan_startup_shutdown(self):
        """Test lifespan context manager."""
        from unittest.mock import AsyncMock, MagicMock

        mock_redis = AsyncMock()
        mock_redis.connect = AsyncMock()
        mock_redis.disconnect = AsyncMock()

        with patch("gateway.main.get_redis", return_value=mock_redis):
            async with lifespan(app):
                pass

        mock_redis.connect.assert_called_once()
        mock_redis.disconnect.assert_called_once()

    def test_signal_handler(self):
        """Test signal handler."""
        # Just test that it doesn't raise an exception
        signal_handler(2, None)

    @patch("gateway.main.uvicorn.run")
    @patch("gateway.main.signal.signal")
    def test_main(self, mock_signal, mock_uvicorn_run):
        """Test main function."""
        from gateway.main import main

        main()

        # Check that signal handlers were set up
        assert mock_signal.call_count == 2
        # Check that uvicorn.run was called
        mock_uvicorn_run.assert_called_once()
