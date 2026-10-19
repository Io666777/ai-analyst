"""Тесты очистки данных (app/cleaner.py)."""

import pandas as pd
import pytest

from app.cleaner import clean, drop_totals, to_date, to_number

# ---------- to_number ----------


def test_to_number_russian_format():
    # Суммы как в русских выгрузках: пробел между тысячами, запятая, "руб."
    result = to_number(pd.Series(["1 200,50", "55,00 руб.", "-300"]))
    assert result.tolist() == [1200.5, 55.0, -300.0]


def test_to_number_garbage_becomes_empty():
    # Пустая строка, текст и пропуск - не ошибка, а пустое значение
    result = to_number(pd.Series(["", "абв", None]))
    assert result.isna().all()


# ---------- to_date ----------


def test_to_date_day_first():
    # 03.04.2025 - это 3 апреля (день первым), а не 4 марта
    result = to_date(pd.Series(["03.04.2025"]))
    assert result.iloc[0] == pd.Timestamp(2025, 4, 3)


def test_to_date_short_year_and_time():
    # Короткий год (как в кафе) и дата со временем (как в салоне)
    result = to_date(pd.Series(["01.10.24", "01.10.2025 09:00"]))
    assert result.iloc[0] == pd.Timestamp(2024, 10, 1)
    assert result.iloc[1] == pd.Timestamp(2025, 10, 1, 9, 0)


def test_to_date_iso_format():
    # Международный формат "год-месяц-день": 2025-03-04 - это 4 марта
    result = to_date(pd.Series(["2025-03-04"]))
    assert result.iloc[0] == pd.Timestamp(2025, 3, 4)


def test_to_date_not_a_date_becomes_empty():
    result = to_date(pd.Series(["Итого"]))
    assert pd.isna(result.iloc[0])


# ---------- drop_totals ----------


def test_drop_totals_default_words():
    table = pd.DataFrame({"Товар": ["Пиво", "ИТОГО:", "  всего по группе"], "Сумма": [1, 2, 3]})
    result = drop_totals(table)
    assert result["Товар"].tolist() == ["Пиво"]


def test_drop_totals_custom_words():
    table = pd.DataFrame({"Товар": ["Пиво", "Сумма по документу"], "Сумма": [1, 2]})
    result = drop_totals(table, words=("сумма по документу",))
    assert result["Товар"].tolist() == ["Пиво"]


# ---------- clean ----------


@pytest.fixture
def dirty_table() -> pd.DataFrame:
    # Маленькая "грязная" таблица: суммы текстом, пробелы, строка "Итого",
    # и итоговая строка с незнакомым названием (у неё нет даты)
    return pd.DataFrame(
        {
            "Дата": ["01.10.2025", "02.10.2025", "Итого", "Сумма по документу"],
            "Товар": [" Пиво ", "Вода", None, None],
            "Сумма": ["10,50", "20", "30,50", "30,50"],
        }
    )


MAPPING = {"Дата": "date", "Товар": "object", "Сумма": "amount"}


def test_clean_result(dirty_table):
    result, _ = clean(dirty_table, MAPPING)
    assert len(result) == 2  # остались только две настоящие продажи
    assert result["Товар"].tolist() == ["Пиво", "Вода"]  # пробелы убраны
    assert result["Сумма"].sum() == 30.5  # суммы стали числами
    assert pd.api.types.is_datetime64_any_dtype(result["Дата"])


def test_clean_report(dirty_table):
    _, report = clean(dirty_table, MAPPING)
    assert report["строк_было"] == 4
    assert report["удалено_итоговых_и_пустых"] == 1  # "Итого"
    assert report["удалено_без_даты"] == 1  # "Сумма по документу"
    assert report["строк_стало"] == 2


def test_clean_does_not_change_input(dirty_table):
    before = dirty_table.copy()
    clean(dirty_table, MAPPING)
    pd.testing.assert_frame_equal(dirty_table, before)  # исходная таблица не изменилась


def test_clean_unknown_column():
    # Опечатка в названии колонки - понятная ошибка, а не тихий неправильный результат
    table = pd.DataFrame({"Дата": ["01.10.2025"]})
    with pytest.raises(ValueError, match="Дат"):
        clean(table, {"Дат": "date"})
