"""Тесты универсальной модели (app/model.py)."""

import pandas as pd
import pytest

from app.model import EVENT_COLUMNS, KIND_SALE, KIND_STOCK, available_fields, to_events

MAPPING = {
    "Дата": "date",
    "Услуга": "object",
    "Мастер": "executor",
    "Клиент": "person",
    "Стоимость": "amount",
}


@pytest.fixture
def cleaned_table() -> pd.DataFrame:
    # Уже очищенная таблица салона: даты - даты, суммы - числа
    return pd.DataFrame(
        {
            "Дата": pd.to_datetime(["2025-10-01", "2025-10-02"]),
            "Услуга": ["Стрижка", "Маникюр"],
            "Мастер": ["Петрова", "Сидорова"],
            "Клиент": ["Иванова Анна", "Лис Сергей"],
            "Стоимость": [45.0, 40.0],
        }
    )


def test_to_events_standard_columns(cleaned_table):
    events = to_events(cleaned_table, MAPPING)
    assert list(events.columns) == EVENT_COLUMNS  # стандартные колонки в стандартном порядке


def test_to_events_keeps_values(cleaned_table):
    events = to_events(cleaned_table, MAPPING)
    assert events["object"].tolist() == ["Стрижка", "Маникюр"]
    assert events["executor"].tolist() == ["Петрова", "Сидорова"]
    assert events["amount"].sum() == 85.0


def test_to_events_drops_personal_data(cleaned_table):
    # Клиент (роль person) - персональные данные, в модель не попадает
    events = to_events(cleaned_table, MAPPING)
    assert "Клиент" not in events.columns
    assert "Иванова Анна" not in events.to_string()


def test_to_events_missing_fields_are_empty(cleaned_table):
    # У салона нет количества и категории - колонки есть, но пустые
    events = to_events(cleaned_table, MAPPING)
    assert events["quantity"].isna().all()
    assert events["category"].isna().all()


def test_to_events_kind(cleaned_table):
    assert (to_events(cleaned_table, MAPPING)["kind"] == KIND_SALE).all()  # по умолчанию продажа
    assert (to_events(cleaned_table, MAPPING, kind=KIND_STOCK)["kind"] == KIND_STOCK).all()


def test_to_events_without_date(cleaned_table):
    with pytest.raises(ValueError, match="дат"):
        to_events(cleaned_table, {"Услуга": "object", "Стоимость": "amount"})


def test_to_events_duplicate_role(cleaned_table):
    # Две колонки с ролью "сумма" - непонятно, какую брать
    with pytest.raises(ValueError, match="amount"):
        to_events(cleaned_table, {**MAPPING, "Мастер": "amount"})


def test_available_fields(cleaned_table):
    events = to_events(cleaned_table, MAPPING)
    assert available_fields(events) == ["date", "object", "amount", "executor"]
