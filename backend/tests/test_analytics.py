"""Тесты аналитики (app/analytics.py) на маленькой таблице, где все ответы считаются в уме.

Продажи:
    10.01.2026        Пиво Лидское   A1  10 шт  100
    20.01.2026        Хлеб           B1   5 шт   50
    05.02.2026        Пиво Лидское   A1  10 шт  100
    28.02.2026 18:00  Пиво Аливария  A2   4 шт   60   <- последний день месяца, со временем
    10.03.2026        Пиво Лидское   A1  20 шт  200
    31.03.2026 15:00  Хлеб           B1  10 шт  100   <- последний день месяца, со временем
    15.04.2026        Пиво Лидское   A1   5 шт   50   <- данные кончаются в середине апреля

По месяцам: январь 150, февраль 160, март 300, апрель 50. Всего 660.
По товарам: Лидское 450, Хлеб 150, Аливария 60.
"""

import pandas as pd
import pytest

from app.analytics import (
    breakdown,
    by_period,
    compare_periods,
    find_item,
    find_items,
    incomplete_periods,
    item_detail,
    last_full_month,
    last_full_month_vs_previous,
    period_total,
)
from app.model import to_events

MAPPING = {
    "Дата": "date",
    "Товар": "object",
    "Группа": "category",
    "Артикул": "attribute",
    "Шт": "quantity",
    "Сумма": "amount",
}


def make_events(rows: list[tuple]) -> pd.DataFrame:
    # (дата, товар, группа, артикул, шт, сумма) -> события универсальной модели
    table = pd.DataFrame(rows, columns=list(MAPPING))
    table["Дата"] = pd.to_datetime(table["Дата"], format="ISO8601")  # с временем и без
    table["Товар"] = table["Товар"].astype("string")
    table["Артикул"] = table["Артикул"].astype("string")
    return to_events(table, MAPPING)


@pytest.fixture
def events() -> pd.DataFrame:
    return make_events(
        [
            ("2026-01-10", "Пиво Лидское", "Напитки", "A1", 10, 100.0),
            ("2026-01-20", "Хлеб", "Хлеб", "B1", 5, 50.0),
            ("2026-02-05", "Пиво Лидское", "Напитки", "A1", 10, 100.0),
            ("2026-02-28 18:00", "Пиво Аливария", "Напитки", "A2", 4, 60.0),
            ("2026-03-10", "Пиво Лидское", "Напитки", "A1", 20, 200.0),
            ("2026-03-31 15:00", "Хлеб", "Хлеб", "B1", 10, 100.0),
            ("2026-04-15", "Пиво Лидское", "Напитки", "A1", 5, 50.0),
        ]
    )


# ---------- by_period ----------


def test_by_period_month(events):
    assert by_period(events, "месяц").tolist() == [150, 160, 300, 50]


def test_by_period_quantity(events):
    assert by_period(events, "месяц", value="quantity").tolist() == [15, 14, 30, 5]


def test_by_period_unknown_period(events):
    with pytest.raises(ValueError, match="квартал"):
        by_period(events, "квартал")


def test_by_period_text_field(events):
    # Артикул - текст, складывать его нельзя
    with pytest.raises(ValueError, match="не числовое"):
        by_period(events, value="Артикул")


def test_by_period_missing_field(events):
    with pytest.raises(ValueError, match="executor"):
        by_period(events, value="executor")


def test_by_period_full_periods_only(events):
    # Данные с 10 января по 15 апреля: январь и апрель неполные - остаются февраль и март
    assert by_period(events, "месяц", full_periods_only=True).tolist() == [160, 300]


def test_incomplete_periods(events):
    assert incomplete_periods(events) == [
        "январь 2026 (данные с 10.01.2026)",
        "апрель 2026 (данные по 15.04.2026)",
    ]
    # Без апреля: март кончается 31.03 (в 15:00) - он полный, неполным остаётся только январь
    until_march = events[events["date"] < "2026-04-01"]
    assert incomplete_periods(until_march) == ["январь 2026 (данные с 10.01.2026)"]


# ---------- period_total и compare_periods ----------


def test_period_total_includes_last_day_with_time(events):
    # 28.02 в 18:00 и 31.03 в 15:00 попадают в свои месяцы
    assert period_total(events, "2026-02-01", "2026-02-28") == 160
    assert period_total(events, "2026-03-01", "2026-03-31") == 300


def test_compare_periods(events):
    # Февраль и март - оба целиком внутри данных, предупреждений нет
    result = compare_periods(events, ("2026-02-01", "2026-02-28"), ("2026-03-01", "2026-03-31"))
    assert result["было"] == 160
    assert result["стало"] == 300
    assert result["изменение"] == 140
    assert result["изменение_%"] == 87.5
    assert result["предупреждения"] == []


def test_compare_periods_partial_month_warns(events):
    # Данные начинаются 10 января: январь покрыт не целиком - честное предупреждение
    result = compare_periods(events, ("2026-01-01", "2026-01-31"), ("2026-03-01", "2026-03-31"))
    assert result["изменение_%"] == 100.0  # 150 -> 300
    assert "2026-01-01" in result["предупреждения"][0]


def test_compare_periods_zero_before(events):
    # В декабре продаж нет: процент не считаем (на ноль делить нельзя)
    result = compare_periods(events, ("2025-12-01", "2025-12-31"), ("2026-01-01", "2026-01-31"))
    assert result["было"] == 0
    assert result["изменение_%"] is None


def test_compare_periods_warns_beyond_data(events):
    # Весь апрель, а данные только по 15 апреля
    result = compare_periods(events, ("2026-03-01", "2026-03-31"), ("2026-04-01", "2026-04-30"))
    assert "выходит за пределы данных" in result["предупреждения"][0]


# ---------- last_full_month и last_full_month_vs_previous ----------


def test_last_full_month_skips_unfinished(events):
    # Данные по 15 апреля - апрель недописан, последний полный месяц - март
    assert last_full_month(events) == pd.Period("2026-03", freq="M")


def test_last_full_month_ends_on_last_day(events):
    # Данные кончаются 31 марта (в 15:00) - март полный
    until_march = events[events["date"] < "2026-04-01"]
    assert last_full_month(until_march) == pd.Period("2026-03", freq="M")


def test_last_full_month_none_when_no_full_month(events):
    # Одна продажа 15 апреля: ни один месяц не покрыт целиком
    assert last_full_month(events[events["date"] >= "2026-04-01"]) is None


def test_last_full_month_vs_previous(events):
    result = last_full_month_vs_previous(events)
    assert result["месяц"] == "март 2026"
    assert result["прошлый_месяц"] == "февраль 2026"
    assert result["было"] == 160
    assert result["стало"] == 300
    # В день: февраль 160 / 28 = 5.71, март 300 / 31 = 9.68 -> рост на 69.4%
    assert result["изменение_в_день_%"] == pytest.approx(69.4, abs=0.1)


def test_last_full_month_vs_previous_too_little_data(events):
    with pytest.raises(ValueError, match="Мало данных"):
        last_full_month_vs_previous(events[events["date"] < "2026-02-01"])


# ---------- breakdown ----------


def test_breakdown_by_object(events):
    result = breakdown(events)
    assert result.index.tolist() == ["Пиво Лидское", "Хлеб", "Пиво Аливария"]
    assert result["amount"].tolist() == [450, 150, 60]
    assert result["доля_%"].iloc[0] == 68.2  # 450 / 660


def test_breakdown_share_from_total_not_from_top(events):
    # Даже если показываем только топ-1, доля считается от всей выручки, а не 100%
    result = breakdown(events, top=1)
    assert len(result) == 1
    assert result["доля_%"].iloc[0] == 68.2


def test_breakdown_worst(events):
    assert breakdown(events, worst=True).index[0] == "Пиво Аливария"


def test_breakdown_by_category_and_attribute(events):
    assert breakdown(events, by="category")["amount"].tolist() == [510, 150]
    assert breakdown(events, by="Артикул").index[0] == "A1"  # дополнительное поле


def test_breakdown_missing_field(events):
    with pytest.raises(ValueError, match="executor"):
        breakdown(events, by="executor")


# ---------- поиск товара ----------


def test_find_item_case_and_part_of_name(events):
    assert find_item(events, "ПИВО ЛИДСКОЕ") == "Пиво Лидское"
    assert find_item(events, "алив") == "Пиво Аливария"


def test_find_item_by_attribute(events):
    # Точное значение признака (артикул), регистр не важен
    assert find_item(events, "a2") == "Пиво Аливария"


def test_find_item_exact_name_wins():
    # "Пиво" - точное название, хотя слово есть и в "Пиво тёмное"
    events = make_events(
        [
            ("2026-01-10", "Пиво", "Напитки", "P1", 1, 10.0),
            ("2026-01-11", "Пиво тёмное", "Напитки", "P2", 1, 10.0),
        ]
    )
    assert find_item(events, "пиво") == "Пиво"


def test_find_items_several(events):
    assert find_items(events, "пиво") == ["Пиво Аливария", "Пиво Лидское"]
    with pytest.raises(ValueError, match="несколько"):
        find_item(events, "пиво")


def test_find_item_not_found(events):
    with pytest.raises(ValueError, match="Не найдено"):
        find_item(events, "кофе")


# ---------- item_detail ----------


def test_item_detail(events):
    detail = item_detail(events, "лидское")
    assert detail["товар"] == "Пиво Лидское"
    assert detail["выручка"] == 450
    assert detail["доля_выручки_%"] == 68.2
    assert detail["количество"] == 45
    assert detail["первая_продажа"] == pd.Timestamp("2026-01-10")
    assert detail["последняя_продажа"] == pd.Timestamp("2026-04-15")
    # Данные с 10.01 по 15.04: январь и апрель неполные - на графике только февраль и март
    assert detail["динамика"].tolist() == [100, 200]
    assert detail["последний_месяц"]["стало"] == 200  # март


def test_item_detail_all_matches(events):
    # "Всё пиво сразу": Лидское 450 + Аливария 60
    detail = item_detail(events, "пиво", all_matches=True)
    assert detail["выручка"] == 510
    assert detail["позиции"] == ["Пиво Аливария", "Пиво Лидское"]


def test_item_detail_full_months_from_all_data(events):
    # Аливарию купили только 28.02. Полные месяцы решаются по ВСЕМ данным, а не по одной
    # её продаже: март полный, просто без продаж - падение на 100%, а не "мало данных"
    detail = item_detail(events, "аливария")
    assert detail["выручка"] == 60
    assert detail["динамика"].tolist() == [60, 0]  # февраль, март
    assert detail["последний_месяц"]["было"] == 60
    assert detail["последний_месяц"]["стало"] == 0
    assert detail["последний_месяц"]["предупреждения"] == []


def test_item_detail_without_two_full_months():
    # Во всех данных меньше двух полных месяцев - сравнивать не с чем, но отчёт всё равно есть
    events = make_events([("2026-01-10", "Хлеб", "Хлеб", "B1", 5, 50.0)])
    detail = item_detail(events, "хлеб")
    assert detail["выручка"] == 50
    assert detail["последний_месяц"] is None
