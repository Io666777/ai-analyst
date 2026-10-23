"""Тесты ручек анализа (app/api/routes/analysis.py): сценарий пользователя - открыл, разметил,
смотрит раздел."""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.sessions import store

client = TestClient(app)


def prepare(file_name: str, data: bytes, mapping: dict[str, str]) -> dict[str, str]:
    # Загрузили свой файл и разметили -> заголовок готовой к анализу сессии
    session_id = client.post("/api/files", files={"file": (file_name, data)}).json()["session_id"]
    headers = {"X-Session-Id": session_id}
    client.put("/api/session/mapping", json={"mapping": mapping}, headers=headers)
    return headers


@pytest.fixture
def shop() -> dict[str, str]:
    # Тестовый магазин: два года данных, с 01.10.2024 по 30.09.2026
    body = client.post("/api/examples/shop.xlsx").json()
    headers = {"X-Session-Id": body["session_id"]}
    client.put("/api/session/mapping", json={"mapping": body["mapping"]}, headers=headers)
    return headers


@pytest.fixture
def short_history() -> dict[str, str]:
    # Данные с 10 января по 10 марта: полный только февраль
    rows = ["10.01.2026;100", "20.01.2026;50", "05.02.2026;70", "28.02.2026;30", "10.03.2026;40"]
    data = "\n".join(["Дата;Сумма", *rows]).encode("utf-8")
    return prepare("short.csv", data, {"Дата": "date", "Сумма": "amount"})


def test_overview(shop):
    response = client.get("/api/analysis/overview", headers=shop)
    assert response.status_code == 200
    body = response.json()

    assert body["currency"] == "р."
    assert [body["date_from"], body["date_to"]] == ["2024-10-01", "2026-09-30"]
    # Все 24 месяца полные - на графике каждый
    assert len(body["monthly"]) == 24
    assert body["monthly"][0]["period"] == "2024-10"
    assert body["monthly"][-1]["period"] == "2026-09"
    assert body["incomplete"] == []

    events = store.get(shop["X-Session-Id"]).events
    september = events[events["date"].dt.strftime("%Y-%m") == "2026-09"]["amount"].sum()
    month = body["last_month"]
    assert month["month"] == "сентябрь 2026"
    assert month["previous_month"] == "август 2026"
    assert month["after"] == pytest.approx(september, abs=0.01)
    assert body["monthly"][-1]["value"] == pytest.approx(september, abs=0.01)
    assert body["total"] == pytest.approx(events["amount"].sum(), abs=0.01)


def test_overview_short_history(short_history):
    body = client.get("/api/analysis/overview", headers=short_history).json()
    # На графике только полный февраль: январь начат не с 1-го, март не закончен
    assert body["monthly"] == [{"period": "2026-02", "value": 100.0}]
    assert body["incomplete"] == [
        "январь 2026 (данные с 10.01.2026)",
        "март 2026 (данные по 10.03.2026)",
    ]
    # Полный месяц один - сравнивать не с чем: вместо цифр - понятная фраза
    assert body["last_month"] is None
    assert "два полных месяца" in body["last_month_note"]


def test_overview_respects_exclusions(shop):
    before = client.get("/api/analysis/overview", headers=shop).json()["total"]
    excluded = client.put(
        "/api/session/settings", json={"exclude": ["Пиво Лидское 0.5"]}, headers=shop
    ).json()["excluded_amount"]
    after = client.get("/api/analysis/overview", headers=shop).json()["total"]
    assert after == pytest.approx(before - excluded, abs=0.01)


# ---------- топ ----------


def test_top_products(shop):
    response = client.get("/api/analysis/top", params={"top": 3}, headers=shop)
    assert response.status_code == 200
    body = response.json()

    assert body["by"] == "object"
    assert len(body["rows"]) == 3
    values = [row["value"] for row in body["rows"]]
    assert values == sorted(values, reverse=True)  # лидер первым
    assert body["rows"][0]["name"] == "Пиво Лидское 0.5"
    # Доля - от всей выручки: у трёх лидеров вместе меньше 100%
    total = client.get("/api/analysis/overview", headers=shop).json()["total"]
    assert body["rows"][0]["share_percent"] == pytest.approx(values[0] / total * 100, abs=0.1)
    assert sum(row["share_percent"] for row in body["rows"]) < 100


def test_top_worst_and_extra_field(shop):
    worst = client.get("/api/analysis/top", params={"worst": True}, headers=shop).json()
    values = [row["value"] for row in worst["rows"]]
    assert values == sorted(values)  # худшие - по возрастанию

    brands = client.get("/api/analysis/top", params={"by": "Бренд"}, headers=shop).json()
    assert brands["by_label"] == "Бренд"  # дополнительное поле - под своим названием
    assert "Лидское" in [row["name"] for row in brands["rows"]]


def test_top_available_fields(shop):
    body = client.get("/api/analysis/top", headers=shop).json()
    available = [choice["value"] for choice in body["available"]]
    assert {"object", "category", "Бренд", "Артикул"} <= set(available)
    assert not {"date", "amount", "quantity"} & set(available)  # даты и числа - не для топа


@pytest.mark.parametrize("by", ["amount", "date", "нет такого"])
def test_top_wrong_field(shop, by):
    response = client.get("/api/analysis/top", params={"by": by}, headers=shop)
    assert response.status_code == 400
    assert "Можно по" in response.json()["detail"]


def test_top_size_limits(shop):
    assert client.get("/api/analysis/top", params={"top": 0}, headers=shop).status_code == 422
    assert client.get("/api/analysis/top", params={"top": 51}, headers=shop).status_code == 422


# ---------- товар ----------


def test_search_items(shop):
    body = client.get("/api/analysis/items", params={"q": "пиво"}, headers=shop).json()
    assert body["items"] == ["Пиво Аливария 0.5", "Пиво Крыніца 1.0", "Пиво Лидское 0.5"]
    assert body["total"] == 3

    by_article = client.get("/api/analysis/items", params={"q": "00-0001"}, headers=shop).json()
    assert by_article["items"] == ["Пиво Лидское 0.5"]  # по артикулу - точно одна позиция


def test_search_items_empty_query(shop):
    assert client.get("/api/analysis/items", params={"q": ""}, headers=shop).status_code == 422


def test_item_detail(shop):
    response = client.get("/api/analysis/item", params={"q": "лидское"}, headers=shop)
    assert response.status_code == 200
    body = response.json()

    assert body["name"] == "Пиво Лидское 0.5"
    assert body["share_percent"] == 27.5  # как в топе
    assert body["quantity"] > 0
    assert [body["first_sale"], body["last_sale"]] == ["2024-10-01", "2026-09-30"]
    assert len(body["monthly"]) == 24  # динамика по всем полным месяцам
    assert body["last_month"]["month"] == "сентябрь 2026"
    assert body["last_month"]["after"] == body["monthly"][-1]["value"]


def test_item_ambiguous_asks_to_clarify(shop):
    response = client.get("/api/analysis/item", params={"q": "пиво"}, headers=shop)
    assert response.status_code == 400
    assert "Уточните" in response.json()["detail"]


def test_item_all_matches(shop):
    body = client.get("/api/analysis/item", params={"q": "пиво", "all": True}, headers=shop).json()
    assert body["name"] == "пиво (позиций: 3)"
    assert len(body["items"]) == 3
    one = client.get("/api/analysis/item", params={"q": "лидское"}, headers=shop).json()
    assert body["amount"] > one["amount"]  # всё пиво больше одного сорта


def test_item_not_found(shop):
    response = client.get("/api/analysis/item", params={"q": "трактор"}, headers=shop)
    assert response.status_code == 404


# ---------- сравнение периодов ----------


def periods(first: tuple[str, str], second: tuple[str, str]) -> dict[str, str]:
    # Параметры адреса для /compare
    return {
        "first_from": first[0],
        "first_to": first[1],
        "second_from": second[0],
        "second_to": second[1],
    }


def total_between(headers: dict[str, str], start: str, end: str) -> float:
    # Выручка с start по end включительно - прямо по событиям сессии
    events = store.get(headers["X-Session-Id"]).events
    dates = events["date"].dt.strftime("%Y-%m-%d")
    return events.loc[(dates >= start) & (dates <= end), "amount"].sum()


def test_compare_march_to_march(shop):
    params = periods(("2025-03-01", "2025-03-31"), ("2026-03-01", "2026-03-31"))
    response = client.get("/api/analysis/compare", params=params, headers=shop)
    assert response.status_code == 200
    body = response.json()

    before = total_between(shop, "2025-03-01", "2025-03-31")
    after = total_between(shop, "2026-03-01", "2026-03-31")
    assert body["first"]["value"] == pytest.approx(before, abs=0.01)
    assert body["second"]["value"] == pytest.approx(after, abs=0.01)
    assert body["first"]["days"] == 31
    assert body["change_percent"] == pytest.approx((after - before) / before * 100, abs=0.1)
    assert body["warnings"] == []


def test_compare_per_day_for_different_lengths(shop):
    # Январь (31 день) против февраля (28): в среднем за день - честнее, чем за месяц
    params = periods(("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-02-28"))
    body = client.get("/api/analysis/compare", params=params, headers=shop).json()
    assert body["first"]["per_day"] == pytest.approx(body["first"]["value"] / 31, abs=0.01)
    assert body["second"]["per_day"] == pytest.approx(body["second"]["value"] / 28, abs=0.01)
    assert body["per_day_change_percent"] > body["change_percent"]  # февраль короче


def test_compare_outside_data(shop):
    # Первый период - до начала данных: было 0, процента нет, есть предупреждение
    params = periods(("2020-01-01", "2020-01-31"), ("2026-01-01", "2026-01-31"))
    body = client.get("/api/analysis/compare", params=params, headers=shop).json()
    assert body["first"]["value"] == 0
    assert body["change_percent"] is None
    assert len(body["warnings"]) == 1


def test_compare_reversed_period(shop):
    params = periods(("2026-03-31", "2026-03-01"), ("2026-04-01", "2026-04-30"))
    response = client.get("/api/analysis/compare", params=params, headers=shop)
    assert response.status_code == 400
    assert "позже конца" in response.json()["detail"]


def test_compare_bad_date(shop):
    params = periods(("2026-02-30", "2026-03-01"), ("2026-04-01", "2026-04-30"))
    assert client.get("/api/analysis/compare", params=params, headers=shop).status_code == 422


def test_overview_before_mapping():
    session_id = client.post("/api/examples/cafe.csv").json()["session_id"]
    response = client.get("/api/analysis/overview", headers={"X-Session-Id": session_id})
    assert response.status_code == 409
