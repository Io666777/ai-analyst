"""Тесты API (app/api/): запросы как от фронта, но без запуска сервера."""

from fastapi.testclient import TestClient

from app.api.main import app
from app.config import FRONTEND_URL

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_swagger_under_api_prefix():
    assert client.get("/api/docs").status_code == 200
    schema = client.get("/api/openapi.json").json()
    assert "/api/health" in schema["paths"]


def test_cors_allows_only_frontend():
    # Браузер перед запросом с другого адреса спрашивает разрешение (preflight-запрос OPTIONS)
    allowed = client.options(
        "/api/health",
        headers={"Origin": FRONTEND_URL, "Access-Control-Request-Method": "GET"},
    )
    assert allowed.headers.get("access-control-allow-origin") == FRONTEND_URL

    stranger = client.options(
        "/api/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in stranger.headers
