"""Тесты хранилища сессий (app/api/sessions.py): время подставляем своими часами."""

import pandas as pd
import pytest

from app.api.sessions import SessionNotFoundError, SessionStore

MINUTE = 60


class FakeClock:
    # Часы, которые идут только когда скажем: store.clock() возвращает now
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(clock) -> SessionStore:
    return SessionStore(ttl=30 * MINUTE, max_sessions=3, clock=clock)


TABLE = pd.DataFrame({"Дата": ["01.10.2025"], "Сумма": [10]})


def test_create_and_get(store):
    session_id = store.create("shop.xlsx", TABLE)
    session = store.get(session_id)
    assert session.file_name == "shop.xlsx"
    assert session.table.equals(TABLE)
    assert session.mapping is None  # колонки ещё не размечены


def test_ids_are_random_and_long(store):
    first, second = store.create("a.csv", TABLE), store.create("b.csv", TABLE)
    assert first != second
    assert len(first) >= 32  # такой номер не подобрать перебором


def test_unknown_id(store):
    with pytest.raises(SessionNotFoundError):
        store.get("выдуманный-номер")


def test_expires_after_ttl(store, clock):
    session_id = store.create("shop.xlsx", TABLE)
    clock.now += 31 * MINUTE  # полчаса без запросов
    with pytest.raises(SessionNotFoundError):
        store.get(session_id)
    assert len(store) == 0  # и памяти она больше не занимает


def test_access_extends_life(store, clock):
    session_id = store.create("shop.xlsx", TABLE)
    clock.now += 20 * MINUTE
    store.get(session_id)  # пользователь работает - сессия продлевается
    clock.now += 20 * MINUTE  # с создания прошло 40 минут, с последнего запроса - 20
    assert store.get(session_id).file_name == "shop.xlsx"


def test_least_recently_used_is_evicted(store, clock):
    first = store.create("1.csv", TABLE)
    second = store.create("2.csv", TABLE)
    third = store.create("3.csv", TABLE)
    clock.now += 1
    store.get(first)  # первую трогали недавно - теперь самая давняя вторая
    fourth = store.create("4.csv", TABLE)  # места только на три - вторая вытесняется

    assert len(store) == 3
    with pytest.raises(SessionNotFoundError):
        store.get(second)
    for session_id in (first, third, fourth):
        store.get(session_id)


def test_delete(store):
    session_id = store.create("shop.xlsx", TABLE)
    store.delete(session_id)
    with pytest.raises(SessionNotFoundError):
        store.get(session_id)
    with pytest.raises(SessionNotFoundError):
        store.delete(session_id)  # повторное удаление - тоже "нет такой сессии"
