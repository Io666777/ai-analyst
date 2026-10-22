"""Сквозные тесты подготовки данных (app/data/prepare.py) на тестовых файлах из data/synthetic."""

import json

import pytest

from app.config import SYNTHETIC_DIR
from app.data import EVENT_COLUMNS, load, prepare_events, to_number

TEST_FILES = ["shop.xlsx", "cafe.csv", "salon.xlsx"]


def read_mapping(file_name: str) -> dict[str, str]:
    # Эталон разметки колонок из .json рядом с тестовым файлом
    path = (SYNTHETIC_DIR / file_name).with_suffix(".json")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("file_name", TEST_FILES)
def test_prepare_events_structure(file_name):
    events, report = prepare_events(SYNTHETIC_DIR / file_name, read_mapping(file_name))
    # Сначала основные колонки в стандартном порядке, после них - дополнительные (если есть)
    assert list(events.columns[: len(EVENT_COLUMNS)]) == EVENT_COLUMNS
    assert events["date"].notna().all()  # у каждого события есть дата
    assert report["строк_стало"] == len(events)
    assert report["удалено_итоговых_и_пустых"] == 1  # строка "Итого"


@pytest.mark.parametrize("file_name", TEST_FILES)
def test_prepare_events_total_matches_file(file_name):
    # Сумма после всей подготовки совпадает со строкой "Итого", которую записал генератор
    mapping = read_mapping(file_name)
    amount_column = next(column for column, role in mapping.items() if role == "amount")
    raw_table = list(load(SYNTHETIC_DIR / file_name).values())[0]
    total_in_file = to_number(raw_table[amount_column]).iloc[-1]  # последняя строка - "Итого"

    events, _ = prepare_events(SYNTHETIC_DIR / file_name, mapping)
    assert events["amount"].sum() == pytest.approx(total_in_file)


def test_prepare_events_exclude():
    # Исключённый товар пропадает из событий, а отчёт говорит, сколько и на какую сумму
    mapping = read_mapping("shop.xlsx")
    full, _ = prepare_events(SYNTHETIC_DIR / "shop.xlsx", mapping)
    events, report = prepare_events(
        SYNTHETIC_DIR / "shop.xlsx", mapping, exclude=["Пиво Лидское 0.5"]
    )
    beer = full["object"] == "Пиво Лидское 0.5"
    assert "Пиво Лидское 0.5" not in events["object"].to_numpy()
    assert report["исключено_строк"] == beer.sum()
    assert report["исключено_на_сумму"] == pytest.approx(full.loc[beer, "amount"].sum())


def test_prepare_events_wrong_sheet():
    with pytest.raises(ValueError, match="Лист2"):
        prepare_events(SYNTHETIC_DIR / "shop.xlsx", read_mapping("shop.xlsx"), sheet="Лист2")
