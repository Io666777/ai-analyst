"""Тесты API (app/api/): запросы как от фронта, но без запуска сервера."""

import pandas as pd
from fastapi.testclient import TestClient

from app.api.dependencies import SESSION_EXPIRED
from app.api.main import app
from app.api.sessions import store
from app.config import FRONTEND_URL

client = TestClient(app)
TABLE = pd.DataFrame({"Дата": ["01.10.2025"], "Сумма": [10]})


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_forget_session():
    session_id = store.create("shop.xlsx", TABLE)
    response = client.delete("/api/session", headers={"X-Session-Id": session_id})
    assert response.status_code == 204
    assert session_id not in store._sessions  # данных на сервере больше нет

    again = client.delete("/api/session", headers={"X-Session-Id": session_id})
    assert again.status_code == 404
    assert again.json()["detail"] == SESSION_EXPIRED
    # Машинный код: по нему фронт отличает "сессия устарела" от "товар не найден"
    assert again.headers["X-Error-Code"] == "session-expired"


def test_expired_session_code_reaches_browser():
    # Фронт на другом адресе: браузер покажет странице код ошибки, только если он разрешён (CORS)
    response = client.get(
        "/api/analysis/overview",
        headers={"X-Session-Id": "expired-session-id", "Origin": FRONTEND_URL},
    )
    assert response.status_code == 404
    assert response.headers["X-Error-Code"] == "session-expired"
    assert "x-error-code" in response.headers["access-control-expose-headers"].lower()


def test_not_found_item_has_no_session_code():
    # Другая 404 ("товар не найден") - без кода сессии: фронт не выкинет пользователя на загрузку
    body = client.post("/api/examples/shop.xlsx").json()
    headers = {"X-Session-Id": body["session_id"]}
    client.put("/api/session/mapping", json={"mapping": body["mapping"]}, headers=headers)
    response = client.get("/api/analysis/item", params={"q": "трактор"}, headers=headers)
    assert response.status_code == 404
    assert "X-Error-Code" not in response.headers


def test_session_header_required():
    # Без номера сессии ручка не выполняется - FastAPI сам отвечает, чего не хватает
    assert client.delete("/api/session").status_code == 422


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
