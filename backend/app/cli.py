"""Консольная версия программы: загрузить файл, разметить колонки, смотреть аналитику и прогноз.

Запуск из папки backend:
    venv\\Scripts\\python.exe -m app.cli
    venv\\Scripts\\python.exe -m app.cli путь\\к\\файлу.xlsx

Здесь только ввод, вывод и меню. Все расчёты - вызовы готовых функций из app/.
print в этом файле уместен: это и есть интерфейс программы.
"""

import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

from app.analytics import (
    breakdown,
    by_period,
    compare_periods,
    incomplete_periods,
    item_detail,
    last_full_month_vs_previous,
)
from app.charts import bar_chart, forecast_chart, line_chart
from app.config import BACKEND_DIR, CURRENCY
from app.forecast import COUNTRY, to_daily
from app.forecast_report import COUNTRY_NAMES, money
from app.loader import EXCEL_SUFFIXES, load
from app.model import exclude_objects, suggest_exclusions
from app.pipeline import STEP_FORECAST, make_forecast, prepare_events

OUTPUT_DIR = BACKEND_DIR / "output"  # сюда сохраняются графики
EXAMPLES_SHOWN = 3  # сколько примеров значений показывать при разметке колонки

# Роли колонок для меню разметки: (роль, как её показать пользователю)
ROLE_CHOICES = [
    ("date", "дата"),
    ("object", "товар / услуга"),
    ("category", "категория"),
    ("quantity", "количество"),
    ("amount", "сумма, деньги"),
    ("price", "цена за единицу (если суммы нет - посчитается сама)"),
    ("executor", "сотрудник"),
    ("receipt", "номер чека"),
    ("attribute", "другой признак (текст: артикул, бренд...)"),
    ("measure", "другое число (скидка...)"),
    ("person", "клиент (в анализ не попадёт)"),
]
ROLE_IGNORE = "ignore"


# ---------- ввод ----------


def ask(question: str) -> str:
    # Спросить у пользователя строку. Убираем по краям:
    # пробелы; кавычки ("Копировать как путь" в Windows их добавляет);
    # невидимую метку кодировки ﻿ (её подставляют некоторые редакторы и PowerShell)
    return input(f"{question} ").strip().strip('"').lstrip("﻿")


def ask_yes(question: str) -> bool:
    return ask(f"{question} (д/н):").lower() in ("д", "да", "y", "yes")


def ask_date(question: str) -> str:
    # Дата в нашем формате "31.03.2026" -> "2026-03-31" для функций аналитики
    while True:
        try:
            return f"{pd.to_datetime(ask(question), dayfirst=True):%Y-%m-%d}"
        except ValueError:
            print("Не понял дату. Пример: 31.03.2026")


# ---------- вывод ----------


def title(text: str) -> None:
    print(f"\n=== {text} ===")


def show_report(report: dict) -> None:
    for key, value in report.items():
        print(f"  {key}: {value}")


def show_figure(figure: Figure, name: str) -> None:
    # Сохраняем график в PNG и открываем его в программе для картинок
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{name}.png"
    figure.savefig(path, dpi=150)
    print(f"График сохранён: {path}")
    if hasattr(os, "startfile"):  # открыть файл умеет только Windows
        os.startfile(path)


# ---------- файл и разметка ----------


def mapping_path(file: Path) -> Path:
    # Разметка хранится рядом с файлом: shop.xlsx -> shop.json
    return file.with_suffix(".json")


def ask_mapping(table: pd.DataFrame) -> dict[str, str]:
    # Для каждой колонки - примеры значений и меню ролей
    menu = "  ".join(f"{number} {label}" for number, (_, label) in enumerate(ROLE_CHOICES, 1))
    print(f"\nРоли: {menu}")
    mapping = {}
    for column in table.columns:
        examples = ", ".join(map(str, table[column].dropna().head(EXAMPLES_SHOWN)))
        while True:
            answer = ask(f"Колонка «{column}» (примеры: {examples}). Роль (Enter - не нужна):")
            if not answer:
                mapping[column] = ROLE_IGNORE
                break
            if answer.isdigit() and 1 <= int(answer) <= len(ROLE_CHOICES):
                mapping[column] = ROLE_CHOICES[int(answer) - 1][0]
                break
            print(f"Введи номер от 1 до {len(ROLE_CHOICES)} или просто Enter")
    return mapping


def get_mapping(file: Path, offer_saved: bool = True) -> dict[str, str]:
    # Сохранённая разметка рядом с файлом - или спрашиваем заново.
    # Файлы разметки программа никогда не удаляет: перезаписывает только с согласия
    saved = mapping_path(file)
    if offer_saved and saved.exists():
        if ask_yes(f"Нашлась сохранённая разметка {saved.name}. Использовать?"):
            return json.loads(saved.read_text(encoding="utf-8"))

    sheets = load(file)
    table = next(iter(sheets.values()))  # первый лист
    print(f"Лист «{next(iter(sheets))}»: {len(table)} строк")
    mapping = ask_mapping(table)
    question = (
        f"Перезаписать сохранённую разметку {saved.name}?"
        if saved.exists()
        else "Сохранить разметку, чтобы не размечать в следующий раз?"
    )
    if ask_yes(question):
        saved.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Сохранено: {saved}")
    return mapping


def open_file(file: Path) -> pd.DataFrame:
    # Файл -> разметка -> события. Разметка не подошла - предлагаем разметить заново
    offer_saved = True
    while True:
        mapping = get_mapping(file, offer_saved)
        try:
            events, report = prepare_events(file, mapping)
        except ValueError as error:
            print(f"Не получилось: {error}")
            print("Давай разметим колонки заново.")
            offer_saved = False  # сохранённая не подошла - второй раз её не предлагаем
            continue
        title("Данные подготовлены")
        show_report(report)
        return events


# ---------- настройки сессии ----------


@dataclass
class Session:
    # Всё, с чем работает меню: данные и настройки, выбранные после открытия файла
    events: pd.DataFrame
    currency: str = CURRENCY
    country: str = COUNTRY


def parse_numbers(answer: str, count: int) -> list[int] | None:
    # "1, 3, 5-7" -> [1, 3, 5, 6, 7]; "все" -> все номера. None - не понял ответ
    if answer.lower() in ("все", "всё", "all"):
        return list(range(1, count + 1))
    numbers = []
    for part in answer.replace(" ", "").split(","):
        first, _, last = part.partition("-")  # "5-7" -> "5", "7"; "3" -> "3", ""
        if not first.isdigit() or (last and not last.isdigit()):
            return None
        numbers.extend(range(int(first), int(last or first) + 1))
    # Пустой список ("3-1" задом наперёд) или номера вне списка - тоже "не понял"
    return numbers if numbers and all(1 <= number <= count for number in numbers) else None


def ask_exclusions(events: pd.DataFrame) -> pd.DataFrame:
    # Программа ПРЕДЛАГАЕТ служебные строки (доставка, комиссии...), а выбирает пользователь:
    # среди предложенных бывают и настоящие товары ("CARRIAGE CLOCK" - часы, а не доставка)
    suggested = suggest_exclusions(events)
    if not suggested:
        return events
    print("\nПохоже на служебные строки, а не товары:")
    for number, name in enumerate(suggested, 1):
        print(f"  {number:>2}  {name}")
    while True:
        answer = ask("Что исключить? Номера через запятую (1,2,5-9), «все» или Enter - ничего:")
        if not answer:
            return events
        numbers = parse_numbers(answer, len(suggested))
        if numbers is not None:
            break
        print(f"Не понял. Пример: 1,3,5-7 (номера от 1 до {len(suggested)})")

    events, report = exclude_objects(events, [suggested[number - 1] for number in numbers])
    excluded_sum = money(report["исключено_на_сумму"])
    print(f"Исключено строк: {report['исключено_строк']} на сумму {excluded_sum}")
    return events


def ask_settings(events: pd.DataFrame) -> Session:
    # Служебные строки, валюта, страна праздников. Enter - значение по умолчанию
    events = ask_exclusions(events)
    currency = ask(f"Валюта (Enter - {CURRENCY}):") or CURRENCY
    countries = ", ".join(f"{code} - {name}" for code, name in COUNTRY_NAMES.items())
    print(f"Страна праздников для прогноза: {countries}")
    while True:  # праздники знаем только для этих стран - другой код уронил бы прогноз
        country = (ask(f"Код страны (Enter - {COUNTRY}):") or COUNTRY).upper()
        if country in COUNTRY_NAMES:
            return Session(events, currency, country)
        print(f"Нет такой страны. Есть: {', '.join(COUNTRY_NAMES)}")


# ---------- пункты меню ----------


def menu_by_month(session: Session) -> None:
    # Только полные месяцы: неполный выглядел бы как обвал продаж
    monthly = by_period(session.events, "месяц", full_periods_only=True)
    title("Выручка по месяцам")
    for month, value in monthly.items():
        print(f"  {month:%m.%Y}  {money(value):>12} {session.currency}")
    skipped = incomplete_periods(session.events)
    if skipped:
        print(f"  Неполные месяцы не показаны: {', '.join(skipped)}")
    figure = line_chart(monthly, "Выручка по месяцам", session.currency)
    show_figure(figure, "выручка_по_месяцам")


def menu_last_month(session: Session) -> None:
    title("Последний полный месяц")
    show_report(last_full_month_vs_previous(session.events))


def menu_compare(session: Session) -> None:
    title("Сравнение двух периодов")
    first = (ask_date("Первый период, с (ДД.ММ.ГГГГ):"), ask_date("по:"))
    second = (ask_date("Второй период, с:"), ask_date("по:"))
    show_report(compare_periods(session.events, first, second))


def menu_top(session: Session) -> None:
    title("Топ товаров по выручке")
    top = breakdown(session.events)
    print(top.to_string())
    show_figure(bar_chart(top, "Топ товаров по выручке", session.currency), "топ_товаров")


def menu_item(session: Session) -> None:
    title("Детально по товару")
    query = ask("Название, его часть или артикул:")
    all_matches = ask_yes("Все подходящие товары вместе?")
    detail = item_detail(session.events, query, all_matches=all_matches)
    show_report({key: value for key, value in detail.items() if key != "динамика"})
    figure = line_chart(detail["динамика"], f"{detail['товар']}: выручка", session.currency)
    show_figure(figure, "товар")


def menu_forecast(session: Session) -> None:
    title("Прогноз")
    print("Считаю: проверяю модели на прошлом и подбираю горизонт. Несколько секунд...")
    result = make_forecast(session.events, country=session.country, currency=session.currency)
    print(result["сообщение"])
    if result["ступенька"] != STEP_FORECAST:
        return
    print("Причины:")
    for reason in result["точность"]["причины"]:
        print(f"  - {reason}")
    chart_title = f"Прогноз на {result['горизонт_дней']} дн. ({result['модель']})"
    daily = to_daily(session.events)
    show_figure(
        forecast_chart(daily, result["прогноз"], chart_title, currency=session.currency), "прогноз"
    )


# Пункты меню: номер -> (название, функция)
MENU: dict[str, tuple[str, Callable[[Session], None]]] = {
    "1": ("выручка по месяцам", menu_by_month),
    "2": ("как прошёл последний месяц", menu_last_month),
    "3": ("сравнить два периода", menu_compare),
    "4": ("топ товаров", menu_top),
    "5": ("детально по товару", menu_item),
    "6": ("прогноз", menu_forecast),
}


def main_menu(session: Session) -> None:
    while True:
        title("Что посмотреть?")
        for number, (label, _) in MENU.items():
            print(f"  {number}  {label}")
        print("  0  выход")
        choice = ask("Номер:")
        if choice == "0":
            return
        if choice not in MENU:
            print("Нет такого пункта")
            continue
        try:
            MENU[choice][1](session)
        except ValueError as error:  # понятные ошибки аналитики: "мало данных", "не найдено"...
            print(f"Не получилось: {error}")


def main() -> None:
    print("AI-аналитик для малого бизнеса")
    file = Path(sys.argv[1] if len(sys.argv) > 1 else ask("Путь к файлу (Excel или CSV):"))
    if not file.exists():
        print(f"Файл не найден: {file}")
        return
    if file.suffix.lower() not in (".csv", *EXCEL_SUFFIXES):
        print(f"Формат {file.suffix} не поддерживается: нужен Excel (.xlsx, .xls) или CSV")
        return
    try:
        main_menu(ask_settings(open_file(file)))
    except (EOFError, KeyboardInterrupt):  # ввод закончился или нажали Ctrl+C
        print()
    print("До свидания!")


if __name__ == "__main__":
    main()
