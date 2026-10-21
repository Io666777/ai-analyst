"""Тесты загрузчика (app/data/loader.py)."""

import pandas as pd

from app.data import column_names, guess_separator


def test_column_names_empty_and_repeated():
    # Пустые ячейки шапки (часто - объединённые ячейки) и повторы -> уникальные названия
    header = pd.Series(["Дата", None, "Сумма", "  ", "Сумма", "Сумма"])
    assert column_names(header) == [
        "Дата",
        "Колонка 2",
        "Сумма",
        "Колонка 4",
        "Сумма (2)",
        "Сумма (3)",
    ]


def test_guess_separator():
    assert guess_separator("Дата;Сумма;Товар") == ";"
    assert guess_separator("Дата,Сумма,Товар") == ","
