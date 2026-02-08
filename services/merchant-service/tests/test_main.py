"""Tests for merchant service main module."""

import pytest
from fastapi.testclient import TestClient

from merchant_service.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

