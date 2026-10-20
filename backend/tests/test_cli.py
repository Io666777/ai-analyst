"""Тесты разбора ввода в консольной версии (app/cli.py)."""

import pandas as pd
import pytest

from app.charts import value_label
from app.cli import ask_settings, parse_numbers


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("1, 3, 5-7", [1, 3, 5, 6, 7]),
        ("все", [1, 2, 3, 4, 5, 6, 7]),
        ("2-2", [2]),
        ("0", None),  # номера с единицы
        ("8", None),  # вне списка
        ("1,abc", None),  # не число
        ("3-1", None),  # диапазон задом наперёд
        ("1,,2", None),  # пустой номер
    ],
)
def test_parse_numbers(answer, expected):
    assert parse_numbers(answer, 7) == expected


def test_ask_settings_repeats_unknown_country(monkeypatch):
    # Неизвестный код страны уронил бы прогноз - программа переспрашивает.
    # Ответы по очереди: валюта, неизвестная страна, правильная страна (маленькими буквами)
    answers = iter(["£", "XX", "gb"])
    monkeypatch.setattr("builtins.input", lambda _question: next(answers))
    events = pd.DataFrame({"date": pd.to_datetime(["2025-10-01"]), "object": ["Хлеб"]})
    session = ask_settings(events)
    assert session.currency == "£"
    assert session.country == "GB"


def test_value_label_currency():
    assert value_label("amount") == "Выручка, р."  # по умолчанию
    assert value_label("amount", "£") == "Выручка, £"
    assert value_label("quantity", "£") == "Количество, шт."  # штуки от валюты не зависят
    assert value_label("Скидка") == "Скидка"  # дополнительное поле - своё название
