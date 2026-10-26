"""Тесты ручек загрузки (app/api/routes/files.py): свой файл и тестовые примеры."""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import files
from app.api.sessions import store
from app.config import SYNTHETIC_DIR

client = TestClient(app)


def upload(name: str, data: bytes):
    # Как браузер отправляет файл из формы: multipart/form-data, поле file
    return client.post("/api/files", files={"file": (name, data)})


def test_upload_csv():
    response = upload("cafe.csv", (SYNTHETIC_DIR / "cafe.csv").read_bytes())
    assert response.status_code == 200
    body = response.json()

    assert store.get(body["session_id"]).file_name == "cafe.csv"  # сессия создана
    assert body["rows"] == 2921  # все строки файла, включая "Итого" - чистка будет при разметке
    assert [column["name"] for column in body["columns"]] == [
        "Дата чека",
        "Позиция",
        "Раздел меню",
        "Кол-во, шт",
        "Выручка, руб",
    ]
    assert body["columns"][0]["examples"] == ["01.10.24", "01.10.24", "01.10.24"]
    # Свой файл: роли угаданы правилами, у каждой - уверенность; человек только проверяет
    assert body["mapping"] == {
        "Дата чека": "date",
        "Позиция": "object",
        "Раздел меню": "category",
        "Кол-во, шт": "quantity",
        "Выручка, руб": "amount",
    }
    assert set(body["confidence"]) == set(body["mapping"])


def test_upload_wrong_format():
    response = upload("notes.txt", b"hello")
    assert response.status_code == 400
    assert "Excel" in response.json()["detail"]


def test_upload_too_large(monkeypatch):
    monkeypatch.setattr(files, "MAX_UPLOAD_BYTES", 10)  # лимит 10 байт - любой файл больше
    response = upload("cafe.csv", b"0123456789-and-more")
    assert response.status_code == 413


def test_upload_empty_file():
    # Пустой файл - понятная ошибка, а не падение сервера
    response = upload("empty.csv", b"")
    assert response.status_code == 400


def test_list_examples():
    response = client.get("/api/examples")
    assert [example["name"] for example in response.json()] == list(files.EXAMPLES)


@pytest.mark.parametrize("name", list(files.EXAMPLES))
def test_open_example_has_ready_mapping(name):
    body = client.post(f"/api/examples/{name}").json()
    column_names = {column["name"] for column in body["columns"]}
    # Разметка есть, и каждая размеченная колонка действительно есть в файле
    assert body["mapping"]
    assert set(body["mapping"]) <= column_names


@pytest.mark.parametrize("name", list(files.EXAMPLES))
def test_example_mapping_is_accepted(name):
    # Готовую разметку примера сервер принимает как есть: все роли - из справочника,
    # иначе на экране разметки список пустой, а «Готово» - ошибка «Неизвестные роли»
    roles = {role["value"] for role in client.get("/api/options").json()["roles"]}
    body = client.post(f"/api/examples/{name}").json()
    assert set(body["mapping"].values()) <= roles

    headers = {"X-Session-Id": body["session_id"]}
    response = client.put(
        "/api/session/mapping", json={"mapping": body["mapping"]}, headers=headers
    )
    assert response.status_code == 200


def test_open_unknown_example():
    assert client.post("/api/examples/secret.xlsx").status_code == 404
