"""Генератор тестовых данных: три "бизнеса" с разным оформлением выгрузок.

Создаёт в data/synthetic:
- shop.xlsx  - магазин, шапка отчёта сверху (как выгрузка из 1С);
- cafe.csv   - кафе, кодировка cp1251, разделитель ";", суммы текстом "1 200,50";
- salon.xlsx - салон, визиты клиентов с ФИО и телефонами (фейковыми).

Рядом с каждым файлом - эталон разметки колонок (*.json): какая колонка что значит.

Запуск из папки backend:
    python -m scripts.generate_synthetic
"""

import json

import numpy as np
import pandas as pd

from app.config import RANDOM_SEED, SYNTHETIC_DIR

# Что заложено в данные - это потом должна "увидеть" аналитика
TREND_PER_DAY = 0.0005  # медленный рост: +0.05% в день, примерно +18% за год
WEEKEND_BOOST = 1.3  # пятница-воскресенье: продаж на 30% больше
YEARLY_AMPLITUDE = 0.2  # годовая сезонность: +-20%
HOLIDAY_BOOST = 1.8  # в праздники продаж на 80% больше
HOLIDAYS = ["01-01", "01-07", "02-23", "03-08", "05-09", "07-03", "11-07", "12-25", "12-31"]

NOISE_SHARE = 0.01  # доля строк с пропуском значения

SHOP_START, SHOP_DAYS = "2024-10-01", 730
CAFE_START, CAFE_DAYS = "2024-10-01", 730
SALON_START, SALON_DAYS = "2025-10-01", 365

# товар: (группа, среднее количество в день, цена)
SHOP_PRODUCTS = {
    "Пиво Лидское 0.5": ("Напитки", 40, 3.5),
    "Пиво Аливария 0.5": ("Напитки", 20, 3.2),
    "Пиво Крыніца 1.0": ("Напитки", 12, 5.4),
    "Вода Боржоми 0.5": ("Напитки", 25, 2.9),
    "Чипсы Lays 140г": ("Снеки", 18, 4.2),
    "Сухарики 3 корочки": ("Снеки", 22, 1.6),
    "Хлеб Нарочанский": ("Хлеб", 30, 1.9),
}
# товар: (артикул, бренд) - дополнительные признаки, как в выгрузках из 1С
SHOP_ATTRIBUTES = {
    "Пиво Лидское 0.5": ("00-0001", "Лидское"),
    "Пиво Аливария 0.5": ("00-0002", "Аливария"),
    "Пиво Крыніца 1.0": ("00-0003", "Крыніца"),
    "Вода Боржоми 0.5": ("00-0010", "Боржоми"),
    "Чипсы Lays 140г": ("00-0020", "Lays"),
    "Сухарики 3 корочки": ("00-0021", "3 корочки"),
    "Хлеб Нарочанский": ("00-0030", "Лидский хлебозавод"),
}
CAFE_PRODUCTS = {
    "Капучино": ("Кофе", 35, 6.5),
    "Американо": ("Кофе", 25, 5.0),
    "Чизкейк": ("Десерты", 12, 9.8),
    "Бизнес-ланч": ("Обеды", 20, 18.4),
}
# услуга: цена
SALON_SERVICES = {
    "Стрижка женская": 45.0,
    "Стрижка мужская": 25.0,
    "Окрашивание": 120.0,
    "Маникюр": 40.0,
    "Укладка": 30.0,
}
SALON_MASTERS = ["Петрова", "Сидорова", "Ковалёва"]
SALON_BASE_VISITS = 12  # среднее количество визитов в день
SALON_CLIENTS_COUNT = 60

# (имена, фамилии) отдельно для женщин и мужчин, чтобы не было "Смирнова Андрей"
NAMES_BY_GENDER = [
    (["Анна", "Мария", "Ольга", "Елена", "Ирина"], ["Иванова", "Кузнецова", "Смирнова", "Новик"]),
    (["Дмитрий", "Сергей", "Андрей", "Павел"], ["Иванов", "Кузнецов", "Ковальчук", "Лис"]),
]


def sales_multiplier(dates: pd.DatetimeIndex) -> np.ndarray:
    """Во сколько раз продажи в каждый день отличаются от обычного уровня.

    Складывается из тренда, выходных, годовой сезонности и праздников.
    """
    days_from_start = (dates - dates[0]).days.to_numpy()
    trend = 1 + TREND_PER_DAY * days_from_start
    weekend = np.where(dates.dayofweek >= 4, WEEKEND_BOOST, 1.0)
    yearly = 1 + YEARLY_AMPLITUDE * np.sin(2 * np.pi * dates.dayofyear.to_numpy() / 365)
    holiday = np.where(np.isin(dates.strftime("%m-%d"), HOLIDAYS), HOLIDAY_BOOST, 1.0)
    return trend * weekend * yearly * holiday


def make_sales(
    products: dict[str, tuple[str, int, float]],
    start: str,
    days: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Дневные продажи по каждому товару.

    Returns:
        Таблица с колонками date, object, category, quantity, amount.
    """
    dates = pd.date_range(start, periods=days, freq="D")
    multiplier = sales_multiplier(dates)
    frames = []
    for name, (group, base_quantity, price) in products.items():
        quantity = rng.poisson(base_quantity * multiplier)  # случайный шум вокруг уровня
        frames.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "object": name,
                    "category": group,
                    "quantity": quantity,
                    "amount": (quantity * price).round(2),
                }
            )
        )
    return pd.concat(frames).sort_values(["date", "object"], ignore_index=True)


def make_clients(rng: np.random.Generator) -> pd.DataFrame:
    """Список выдуманных клиентов: ФИО и телефон."""
    names = []
    for _ in range(SALON_CLIENTS_COUNT):
        first_names, last_names = NAMES_BY_GENDER[rng.integers(0, len(NAMES_BY_GENDER))]
        names.append(f"{rng.choice(last_names)} {rng.choice(first_names)}")
    phones = [
        f"+375 (29) {rng.integers(100, 999)}-{rng.integers(10, 99)}-{rng.integers(10, 99)}"
        for _ in range(SALON_CLIENTS_COUNT)
    ]
    return pd.DataFrame({"name": names, "phone": phones})


def make_salon_visits(rng: np.random.Generator) -> pd.DataFrame:
    """Визиты в салон: каждая строка - один клиент на одной услуге."""
    dates = pd.date_range(SALON_START, periods=SALON_DAYS, freq="D")
    visits_per_day = rng.poisson(SALON_BASE_VISITS * sales_multiplier(dates))
    visit_days = pd.DatetimeIndex(np.repeat(dates.to_numpy(), visits_per_day))
    count = len(visit_days)

    hours = rng.integers(9, 20, count)  # салон работает с 9 до 20
    visit_times = visit_days + pd.to_timedelta(hours, unit="h")
    services = rng.choice(list(SALON_SERVICES), count)
    clients = make_clients(rng).iloc[rng.integers(0, SALON_CLIENTS_COUNT, count)]

    return pd.DataFrame(
        {
            "Дата визита": visit_times.strftime("%d.%m.%Y %H:%M"),
            "Услуга": services,
            "Мастер": rng.choice(SALON_MASTERS, count),
            "Клиент": clients["name"].to_numpy(),
            "Телефон": clients["phone"].to_numpy(),
            "Стоимость": [SALON_SERVICES[s] for s in services],
        }
    )


def add_noise(df: pd.DataFrame, value_column: str, rng: np.random.Generator) -> pd.DataFrame:
    """Портит данные как в реальной выгрузке: пропуски и строка "Итого" в конце."""
    result = df.copy()
    broken_rows = rng.random(len(result)) < NOISE_SHARE
    result.loc[broken_rows, value_column] = np.nan
    total_row = {column: None for column in result.columns}
    total_row[result.columns[0]] = "Итого"
    total_row[value_column] = result[value_column].sum()
    return pd.concat([result, pd.DataFrame([total_row])], ignore_index=True)


def money_as_text(value: float) -> str:
    """1200.5 -> '1 200,50' - так суммы выглядят в русскоязычных выгрузках."""
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def save_etalon(name: str, roles: dict[str, str]) -> None:
    """Сохраняет эталон разметки: какая колонка файла что значит."""
    path = SYNTHETIC_DIR / f"{name}.json"
    path.write_text(json.dumps(roles, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_shop(rng: np.random.Generator) -> None:
    """Магазин: Excel с шапкой отчёта над таблицей."""
    sales = make_sales(SHOP_PRODUCTS, SHOP_START, SHOP_DAYS, rng)
    table = pd.DataFrame(
        {
            "Дата": sales["date"].dt.strftime("%d.%m.%Y"),
            "Артикул": sales["object"].map(lambda name: SHOP_ATTRIBUTES[name][0]),
            "Номенклатура": sales["object"],
            "Бренд": sales["object"].map(lambda name: SHOP_ATTRIBUTES[name][1]),
            "Группа": sales["category"],
            "Количество": sales["quantity"],
            "Сумма": sales["amount"],
        }
    )
    table = add_noise(table, "Сумма", rng)

    period = f"{table['Дата'].iloc[0]} - {table['Дата'].iloc[-2]}"
    title = pd.DataFrame([["Отчёт о продажах"], [f"Период: {period}"]])
    with pd.ExcelWriter(SYNTHETIC_DIR / "shop.xlsx") as writer:
        title.to_excel(writer, header=False, index=False)
        table.to_excel(writer, startrow=3, index=False)

    save_etalon(
        "shop",
        {
            "Дата": "date",
            "Артикул": "attribute",
            "Номенклатура": "object",
            "Бренд": "attribute",
            "Группа": "category",
            "Количество": "quantity",
            "Сумма": "amount",
        },
    )


def generate_cafe(rng: np.random.Generator) -> None:
    """Кафе: CSV в старой кодировке, суммы текстом."""
    sales = make_sales(CAFE_PRODUCTS, CAFE_START, CAFE_DAYS, rng)
    table = pd.DataFrame(
        {
            "Дата чека": sales["date"].dt.strftime("%d.%m.%y"),
            "Позиция": sales["object"],
            "Раздел меню": sales["category"],
            "Кол-во, шт": sales["quantity"],
            "Выручка, руб": sales["amount"],
        }
    )
    table = add_noise(table, "Выручка, руб", rng)
    table["Выручка, руб"] = table["Выручка, руб"].map(money_as_text, na_action="ignore")
    table.to_csv(SYNTHETIC_DIR / "cafe.csv", sep=";", index=False, encoding="cp1251")

    save_etalon(
        "cafe",
        {
            "Дата чека": "date",
            "Позиция": "object",
            "Раздел меню": "category",
            "Кол-во, шт": "quantity",
            "Выручка, руб": "amount",
        },
    )


def generate_salon(rng: np.random.Generator) -> None:
    """Салон: визиты клиентов с персональными данными (выдуманными)."""
    table = add_noise(make_salon_visits(rng), "Стоимость", rng)
    table.to_excel(SYNTHETIC_DIR / "salon.xlsx", index=False)

    save_etalon(
        "salon",
        {
            "Дата визита": "date",
            "Услуга": "object",
            "Мастер": "executor",
            "Клиент": "person",
            "Телефон": "phone",
            "Стоимость": "amount",
        },
    )


def main() -> None:
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    # У каждого бизнеса свой генератор случайных чисел: изменения в одном бизнесе
    # (например, новый товар в магазине) не сдвигают данные остальных
    generate_shop(np.random.default_rng(RANDOM_SEED))
    generate_cafe(np.random.default_rng(RANDOM_SEED + 1))
    generate_salon(np.random.default_rng(RANDOM_SEED + 2))
    for path in sorted(SYNTHETIC_DIR.glob("*.*")):
        print(f"{path.name:<12} {path.stat().st_size / 1024:>8.1f} КБ")


if __name__ == "__main__":
    main()
