"""Автоопределение ролей колонок правилами: по названию и по значениям, без нейросети.

Каждой колонке - роль и уверенность от 0 до 1. Уверенность низкая - интерфейс просит
проверить колонку (дальше по плану: нейросеть и уточняющие вопросы, этапы 2.2 и 2.3).
"""

import re

import pandas as pd

from app.data.cleaner import to_date
from app.data.model import FIELDS, ROLE_ATTRIBUTE, ROLE_IGNORE, ROLE_MEASURE

SAMPLE_SIZE = 500  # смотрим не все строки, а выборку - иначе медленно на больших файлах
SHARE_NEEDED = 0.9  # колонка "из дат" или "из чисел", если так выглядят 9 значений из 10
FEW_UNIQUE = 30  # мало разных значений - скорее категория, много - скорее товар

# Уверенность: название и значения согласны / только значения / просто догадка
SURE = 0.9
BY_VALUES = 0.75
GUESS = 0.4
# Ниже 0.7 фронт просит проверить колонку (CONFIDENT в features/map-columns)

# Подсказки в названии колонки: слово названия начинается с подсказки ("кол" -> "Кол-во").
# Порядок важен - выигрывает первая роль: "Дата чека" - дата, а не чек;
# "Цена со скидкой" - цена, а не скидка; "Группа товаров" - категория, а не товар
NAME_HINTS: list[tuple[str, tuple[str, ...]]] = [
    ("date", ("дата", "date", "время", "time", "day", "день", "период")),
    ("person", ("клиент", "покупател", "фио", "телефон", "email", "почта", "customer",
                "client", "phone", "mail")),
    ("receipt", ("чек", "документ", "накладн", "заказ", "invoice", "receipt", "order")),
    ("price", ("цена", "price", "тариф")),
    ("quantity", ("кол", "шт", "qty", "quantity", "units", "объём", "объем")),
    (ROLE_MEASURE, ("скидк", "себестоим", "наценк", "discount", "cost", "margin")),
    ("amount", ("сумма", "выручк", "стоимост", "оборот", "доход", "руб", "amount", "revenue",
                "sales", "total")),
    ("executor", ("мастер", "сотрудник", "продав", "кассир", "менеджер", "seller", "employee",
                  "staff", "cashier")),
    ("category", ("групп", "категор", "раздел", "вид", "category", "group", "type")),
    ("object", ("товар", "номенклатур", "наименован", "позиц", "услуг", "назван", "product",
                "item", "description", "service")),
    (ROLE_ATTRIBUTE, ("артикул", "бренд", "код", "марка", "производит", "филиал", "магазин",
                      "страна", "sku", "brand", "code", "store", "country")),
]  # fmt: skip

NUMBER_ROLES = ("quantity", "amount", "price", ROLE_MEASURE)
TEXT_ROLES = ("object", "category", "executor", "person", "receipt", ROLE_ATTRIBUTE)

# Как выглядят значения: число (можно с валютой), дата, телефон, email
NUMBER_PATTERN = re.compile(r"^[-−]?[\d\s .,]+\s*(р\.?|руб\.?|byn|usd|\$|€|£|шт\.?)?$", re.I)
DATE_PATTERN = re.compile(r"\d{1,4}[./-]\d{1,2}[./-]\d{1,4}")
PHONE_PATTERN = re.compile(r"^\+?[\d\s()\-]+$")
PHONE_MIN_DIGITS = 9  # в телефоне цифр много: артикул "00-0010" - не телефон


def name_role(name: str) -> str | None:
    # Роль по названию: "Кол-во, шт" -> quantity, "InvoiceDate" -> date. Нет подсказки - None
    spaced = re.sub(r"([a-zа-яё])([A-ZА-ЯЁ])", r"\1 \2", name)  # "UnitPrice" -> "Unit Price"
    words = re.findall(r"[a-zа-яё0-9]+", spaced.lower())
    for role, hints in NAME_HINTS:
        if any(word.startswith(hint) for word in words for hint in hints):
            return role
    return None


def is_phone(value: str) -> bool:
    # "+375 (29) 111-22-33" - телефон; "00-0010" - нет: мало цифр
    digits = sum(char.isdigit() for char in value)
    return bool(PHONE_PATTERN.match(value)) and digits >= PHONE_MIN_DIGITS


def share(values: pd.Series, check) -> float:
    # Какая доля значений проходит проверку: 0.95 - почти все
    return float(values.map(check).mean()) if len(values) else 0.0


def value_kind(values: pd.Series) -> str:
    # На что похожи значения: empty, date, number, phone, email, few (мало разных), text
    if values.empty:
        return "empty"
    if pd.api.types.is_datetime64_any_dtype(values):
        return "date"
    if pd.api.types.is_numeric_dtype(values):
        return "number"
    text = values.astype(str).str.strip()
    if share(text, lambda value: bool(DATE_PATTERN.search(value))) >= SHARE_NEEDED:
        if to_date(text).notna().mean() >= SHARE_NEEDED:
            return "date"
    if share(text, lambda value: bool(NUMBER_PATTERN.match(value))) >= SHARE_NEEDED:
        return "number"
    if share(text, lambda value: "@" in value) >= SHARE_NEEDED:
        return "email"
    if share(text, is_phone) >= SHARE_NEEDED:
        return "phone"
    return "few" if text.nunique() <= FEW_UNIQUE else "text"


def fits(role: str, kind: str) -> bool:
    # Согласны ли название и значения: "Сумма" из чисел - да, "Сумма" из слов - нет
    if role == "date":
        return kind == "date"
    if role in NUMBER_ROLES:
        return kind == "number"
    if role == "person":
        return kind in ("phone", "email", "text", "few")
    if role in TEXT_ROLES:
        return kind in ("text", "few", "number")  # номер чека и артикул бывают числами
    return False


def role_by_values(kind: str) -> tuple[str, float]:
    # Название ничего не подсказало - роль по одним значениям
    if kind == "empty":
        return ROLE_IGNORE, SURE
    if kind == "date":
        return "date", BY_VALUES
    if kind in ("phone", "email"):
        return "person", BY_VALUES  # личные данные - в анализ не попадут
    if kind == "number":
        return "amount", GUESS  # число без подсказки: может быть и деньгами, и штуками
    if kind == "few":
        return "category", GUESS
    return "object", GUESS


def fallback(role: str, kind: str) -> str:
    # Роль уже занята другой колонкой (две колонки "Дата") - запасная: число - показатель,
    # текст - признак, вторая дата не нужна
    if role == "date" or kind in ("empty", "date"):
        return ROLE_IGNORE
    return ROLE_MEASURE if kind == "number" else ROLE_ATTRIBUTE


def detect_roles(table: pd.DataFrame) -> dict[str, tuple[str, float]]:
    # Колонка -> (роль, уверенность). Основная роль (дата, товар, сумма...) - у одной колонки:
    # её получает самая уверенная, остальным - запасная роль
    guesses = {}
    for column in table.columns:
        kind = value_kind(table[column].dropna().head(SAMPLE_SIZE))
        role = name_role(str(column))
        if role and fits(role, kind):
            guesses[column] = (role, SURE, kind)
        else:
            guesses[column] = (*role_by_values(kind), kind)

    result: dict[str, tuple[str, float]] = {}
    taken: set[str] = set()
    for column, (role, confidence, kind) in sorted(
        guesses.items(), key=lambda item: -item[1][1]
    ):  # сначала самые уверенные: им достаются основные роли
        if role in FIELDS and role in taken:
            role, confidence = fallback(role, kind), GUESS
        taken.add(role)
        result[column] = (role, confidence)
    return {column: result[column] for column in table.columns}  # порядок - как в файле
