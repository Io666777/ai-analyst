"""Тесты универсальной модели (app/model.py)."""

import pandas as pd
import pytest

from app.model import (
    EVENT_COLUMNS,
    KIND_SALE,
    KIND_STOCK,
    available_fields,
    exclude_objects,
    extra_fields,
    numeric_fields,
    suggest_exclusions,
    to_events,
)

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


# ---------- дополнительные поля: признаки и показатели ----------


@pytest.fixture
def table_with_extras(cleaned_table) -> pd.DataFrame:
    # Та же таблица + колонки, которых нет в каталоге основных полей
    return cleaned_table.assign(Артикул=["00012", "А-7"], Скидка=[5.0, 0.0])


EXTRA_MAPPING = {**MAPPING, "Артикул": "attribute", "Скидка": "measure"}


def test_extras_kept_under_own_names(table_with_extras):
    events = to_events(table_with_extras, EXTRA_MAPPING)
    assert list(events.columns[: len(EVENT_COLUMNS)]) == EVENT_COLUMNS  # основные - первыми
    assert extra_fields(events) == ["Артикул", "Скидка"]  # дополнительные - после них
    assert events["Артикул"].tolist() == ["00012", "А-7"]


def test_extras_in_available_and_numeric_fields(table_with_extras):
    events = to_events(table_with_extras, EXTRA_MAPPING)
    assert "Артикул" in available_fields(events)
    assert numeric_fields(events) == ["amount", "Скидка"]  # артикул - текст, его не складывают


def test_extras_name_clash(table_with_extras):
    # Дополнительное поле не может называться как основное - иначе одно затрёт другое
    table = table_with_extras.rename(columns={"Артикул": "amount"})
    with pytest.raises(ValueError, match="amount"):
        to_events(table, {**MAPPING, "amount": "attribute"})


def test_amount_from_price_and_quantity():
    # В выгрузке нет суммы, но есть цена и количество - сумму программа считает сама
    table = pd.DataFrame(
        {"Дата": pd.to_datetime(["2025-10-01"] * 2), "Цена": [2.5, 4.0], "Кол-во": [4, -1]}
    )
    events = to_events(table, {"Дата": "date", "Цена": "price", "Кол-во": "quantity"})
    assert events["amount"].tolist() == [10.0, -4.0]  # возврат (-1 шт) уменьшает выручку
    assert "price" not in numeric_fields(events)  # цены складывать бессмысленно
    assert "amount" in numeric_fields(events)


def test_amount_from_file_wins_over_price():
    # Если сумма в файле есть - берём её, а не пересчитываем
    table = pd.DataFrame(
        {"Дата": pd.to_datetime(["2025-10-01"]), "Цена": [2.5], "Кол-во": [4], "Сумма": [9.0]}
    )
    mapping = {"Дата": "date", "Цена": "price", "Кол-во": "quantity", "Сумма": "amount"}
    assert to_events(table, mapping)["amount"].tolist() == [9.0]  # со скидкой, а не 10


# ---------- служебные строки ----------


@pytest.fixture
def with_service_rows() -> pd.DataFrame:
    names = ["DOTCOM POSTAGE", "COFFEE MUG", "AMAZON FEE", "Доставка курьером", "Пиво"]
    table = pd.DataFrame(
        {
            "Дата": pd.to_datetime(["2025-10-01"] * 5),
            "Товар": pd.Series(names, dtype="string"),
            "Сумма": [10.0, 5.0, 3.0, 7.0, 2.0],
        }
    )
    return to_events(table, {"Дата": "date", "Товар": "object", "Сумма": "amount"})


def test_suggest_exclusions_whole_words(with_service_rows):
    # "fee" находит AMAZON FEE, но не COFFEE MUG; русские слова тоже ищутся
    assert suggest_exclusions(with_service_rows) == [
        "AMAZON FEE",
        "DOTCOM POSTAGE",
        "Доставка курьером",
    ]


def test_exclude_objects(with_service_rows):
    # Регистр не важен; отчёт - сколько строк и на какую сумму убрано
    events, report = exclude_objects(with_service_rows, ["dotcom postage", "AMAZON FEE"])
    assert events["object"].tolist() == ["COFFEE MUG", "Доставка курьером", "Пиво"]
    assert report["исключено_строк"] == 2
    assert report["исключено_на_сумму"] == 13.0
    assert report["исключены"] == ["AMAZON FEE", "DOTCOM POSTAGE"]


def test_personal_data_not_kept_as_extra(table_with_extras):
    # Даже рядом с дополнительными полями клиент в модель не попадает
    events = to_events(table_with_extras, EXTRA_MAPPING)
    assert "Клиент" not in events.columns
