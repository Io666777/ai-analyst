"""Тесты подписей графиков (app/charts.py)."""

from app.charts import value_label


def test_value_label_currency():
    assert value_label("amount") == "Выручка, р."  # по умолчанию
    assert value_label("amount", "£") == "Выручка, £"
    assert value_label("quantity", "£") == "Количество, шт."  # штуки от валюты не зависят
    assert value_label("Скидка") == "Скидка"  # дополнительное поле - своё название
