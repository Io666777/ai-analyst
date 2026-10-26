"""Тесты ручек настройки (app/api/routes/setup.py): справочник, разметка, настройки."""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import NOT_PREPARED
from app.api.main import app
from app.api.sessions import store

client = TestClient(app)


@pytest.fixture
def opened() -> tuple[dict[str, str], dict[str, str]]:
    # Открыли тестовый магазин: (заголовок с номером сессии, эталонная разметка)
    body = client.post("/api/examples/shop.xlsx").json()
    return {"X-Session-Id": body["session_id"]}, body["mapping"]


@pytest.fixture
def prepared(opened) -> dict[str, str]:
    # Открыли и разметили - заголовок готовой к анализу сессии
    headers, mapping = opened
    client.put("/api/session/mapping", json={"mapping": mapping}, headers=headers)
    return headers


def test_options():
    body = client.get("/api/options").json()
    roles = {choice["value"] for choice in body["roles"]}
    assert {"date", "object", "amount", "price", "ignore"} <= roles
    assert {choice["value"] for choice in body["countries"]} >= {"BY", "GB"}
    assert body["default_country"] == "BY"


def test_mapping_prepares_events(opened):
    headers, mapping = opened
    response = client.put("/api/session/mapping", json={"mapping": mapping}, headers=headers)
    assert response.status_code == 200
    body = response.json()

    report = body["report"]
    assert report["removed_totals_and_empty"] == 1  # строка "Итого"
    assert report["rows_after"] == report["rows_before"] - 1 - report["removed_without_date"]
    assert {"date", "object", "amount", "Бренд"} <= set(body["fields"])
    assert body["date_from"] == "2024-10-01"
    assert body["date_to"] == "2026-09-30"

    session = store.get(headers["X-Session-Id"])
    assert len(session.events) == report["rows_after"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"Сумма": "money"}, "Неизвестные роли: money"),  # опечатка в роли
        ({"Нет такой": "object"}, "нет колонок"),  # колонки нет в файле
        ({"Дата": "ignore"}, "дат"),  # без даты события не привязать ко времени
        ({"Сумма": "ignore", "Количество": "ignore"}, "сумм"),  # нечего считать
    ],
)
def test_mapping_errors(opened, change, message):
    headers, mapping = opened
    response = client.put(
        "/api/session/mapping", json={"mapping": {**mapping, **change}}, headers=headers
    )
    assert response.status_code == 400
    assert message in response.json()["detail"]


def test_settings_before_mapping(opened):
    headers, _ = opened
    response = client.put("/api/session/settings", json={}, headers=headers)
    assert response.status_code == 409
    assert response.json()["detail"] == NOT_PREPARED


def test_settings_exclude_and_currency(prepared):
    session = store.get(prepared["X-Session-Id"])
    beer = session.prepared["object"] == "Пиво Лидское 0.5"

    response = client.put(
        "/api/session/settings",
        json={"exclude": ["Пиво Лидское 0.5"], "currency": "$", "country": "gb"},
        headers=prepared,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["excluded_rows"] == beer.sum()
    assert body["excluded_amount"] == pytest.approx(session.prepared.loc[beer, "amount"].sum())
    assert body["country"] == "GB"  # регистр не важен

    assert "Пиво Лидское 0.5" not in session.events["object"].to_numpy()
    assert len(session.prepared) == len(session.events) + beer.sum()  # исходные события целы
    assert session.currency == "$"


def test_settings_unknown_country(prepared):
    response = client.put("/api/session/settings", json={"country": "XX"}, headers=prepared)
    assert response.status_code == 400
    assert "XX" in response.json()["detail"]


def test_new_mapping_resets_settings(prepared, opened):
    client.put("/api/session/settings", json={"exclude": ["Пиво Лидское 0.5"]}, headers=prepared)
    session = store.get(prepared["X-Session-Id"])
    session.cache["прогноз"] = "старый"

    _, mapping = opened
    client.put("/api/session/mapping", json={"mapping": mapping}, headers=prepared)
    assert session.exclude == []  # исключения от старой разметки сброшены
    assert session.cache == {}  # и посчитанное тоже
