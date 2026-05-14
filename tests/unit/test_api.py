"""Unit tests for src/myproject/api.py."""

from fastapi.testclient import TestClient

from src.myproject.api import app


def test_api_health_check():
    """Verify the health endpoint returns 200 OK."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


def test_api_serve_simulator():
    """Verify the root endpoint serves the HTML UI."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Neon Trompo" in response.text
