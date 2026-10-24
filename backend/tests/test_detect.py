"""Тесты автоопределения ролей колонок (app/data/detect.py)."""

import json

import pandas as pd
import pytest

from app.config import SYNTHETIC_DIR
from app.data import detect_roles, load
from app.data.detect import name_role

EXAMPLES = ["shop.xlsx", "cafe.csv", "salon.xlsx"]


@pytest.mark.parametrize("name", EXAMPLES)
def test_guesses_etalon_mapping(name):
    # Тестовые бизнесы - как свои файлы: правила угадывают эталонную разметку целиком
    path = SYNTHETIC_DIR / name
    table = next(iter(load(path).values()))
    etalon = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))

    guesses = detect_roles(table)
    assert {column: role for column, (role, _) in guesses.items()} == etalon
    assert all(confidence >= 0.7 for _, confidence in guesses.values())  # и уверенно


@pytest.mark.parametrize(
    ("column", "role"),
    [
        ("Кол-во, шт", "quantity"),
        ("Выручка, руб", "amount"),
        ("Дата чека", "date"),  # дата, а не чек: дата раньше в списке подсказок
        ("Номер чека", "receipt"),
        ("Цена со скидкой", "price"),
        ("Группа товаров", "category"),
        ("Наименование товара", "object"),
        ("InvoiceDate", "date"),  # английские названия слитно: Invoice + Date
        ("UnitPrice", "price"),
        ("CustomerID", "person"),
        ("StockCode", "attribute"),
        ("Комментарий", None),
    ],
)
def test_name_role(column, role):
    assert name_role(column) == role


def test_values_decide_without_name_hint():
    # Названия ничего не говорят - решают значения
    table = pd.DataFrame(
        {
            "A": ["01.10.2026", "02.10.2026", "03.10.2026"],
            "B": ["+375 (29) 111-22-33", "+375 (29) 444-55-66", "+375 (33) 777-88-99"],
            "C": [None, None, None],
        }
    )
    roles = {column: role for column, (role, _) in detect_roles(table).items()}
    assert roles == {"A": "date", "B": "person", "C": "ignore"}


def test_name_and_values_disagree_is_unsure():
    # "Сумма" из слов: название говорит "деньги", значения - нет. Роль - догадка, уверенность низкая
    table = pd.DataFrame({"Дата": ["01.10.2026"] * 3, "Сумма": ["много", "мало", "средне"]})
    role, confidence = detect_roles(table)["Сумма"]
    assert role != "amount"
    assert confidence < 0.7


def test_text_with_numbers_is_not_a_number():
    # "Пиво 0.5" - товар, а не число, хотя в нём есть цифры
    table = pd.DataFrame({"X": [f"Пиво {i} 0.5" for i in range(50)]})
    assert detect_roles(table)["X"][0] == "object"


def test_main_role_goes_to_one_column():
    # Две колонки с датой: основная роль - одной, вторая не нужна
    table = pd.DataFrame(
        {
            "Дата заказа": ["01.10.2026", "02.10.2026"],
            "Дата доставки": ["03.10.2026", "04.10.2026"],
            "Сумма": [100, 200],
        }
    )
    roles = [role for role, _ in detect_roles(table).values()]
    assert roles.count("date") == 1
    assert "ignore" in roles
