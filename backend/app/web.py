"""Страничка в браузере: загрузить файл, разметить колонки, смотреть аналитику и прогноз.

Запуск из папки backend:
    venv\\Scripts\\python.exe -m streamlit run app/web.py

Streamlit при каждом клике выполняет этот файл заново, сверху вниз. Поэтому тяжёлое
(чтение файла, подготовка, прогноз) запоминаем: второй раз - мгновенно.
Здесь только вывод на экран - все расчёты в готовых функциях из app/, как и в cli.py.

Данные пользователя не хранятся: файл читается из временной папки, которая сразу
удаляется, а всё запомненное живёт в памяти сессии и пропадает, когда закрывают вкладку.
"""

import hashlib
import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.analytics import (
    breakdown,
    by_period,
    compare_periods,
    incomplete_periods,
    item_detail,
    last_full_month_vs_previous,
)
from app.charts import bar_chart, forecast_chart, line_chart
from app.cli import ROLE_CHOICES, ROLE_IGNORE, mapping_path
from app.config import CURRENCY, SYNTHETIC_DIR
from app.forecast import COUNTRY, to_daily
from app.forecast_report import COUNTRY_NAMES, money
from app.loader import EXCEL_SUFFIXES, load
from app.model import FIELDS, available_fields, exclude_objects, numeric_fields, suggest_exclusions
from app.pipeline import STEP_FORECAST, make_forecast, prepare_table

EXAMPLES = ["shop.xlsx", "cafe.csv", "salon.xlsx"]  # тестовые бизнесы из data/synthetic
EXAMPLES_SHOWN = 3  # сколько примеров значений показывать при разметке колонки
ROLE_LABELS = {ROLE_IGNORE: "— не нужна —", **dict(ROLE_CHOICES)}
# Поля, по которым топ не строят: дата, цена за штуку, номер чека
NOT_GROUPED = ("date", "price", "receipt")


# ---------- память сессии ----------


def remembered(key: tuple, compute: Callable[[], Any], message: str) -> Any:
    # Посчитать один раз и запомнить - как st.cache_data, но с важным отличием:
    # st.cache_data общий для ВСЕХ посетителей сервера, а эта память - у каждого своя
    # (st.session_state) и исчезает, когда посетитель закрывает вкладку
    cache = st.session_state.setdefault("cache", {})
    if key not in cache:
        with st.spinner(message):
            cache[key] = compute()
    return cache[key]


def forget_previous_file(file_id: str) -> None:
    # Открыли другой файл - всё запомненное о прежнем удаляем, а не копим в памяти
    if st.session_state.get("file_id") != file_id:
        st.session_state["file_id"] = file_id
        st.session_state["cache"] = {}
        st.session_state["forecast"] = False


def read_table(name: str, data: bytes) -> pd.DataFrame:
    # Файл -> таблица без сохранения на диск сервера. Функциям чтения нужен путь, поэтому
    # кладём файл во временную папку, читаем, и папка удаляется вместе с файлом
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / Path(name).name  # имя без чужих папок: "../x.csv" -> "x.csv"
        path.write_bytes(data)
        return next(iter(load(path).values()))  # первый лист


# ---------- боковая панель: файл, разметка, настройки ----------


def choose_file() -> tuple[str, bytes] | None:
    # Свой файл или тестовый пример -> (имя файла, содержимое)
    uploaded = st.sidebar.file_uploader("Файл с продажами", type=["csv", *EXCEL_SUFFIXES])
    st.sidebar.caption("Файл не сохраняется: он в памяти, пока открыта вкладка")
    if uploaded is not None:
        return uploaded.name, uploaded.getvalue()
    example = st.sidebar.selectbox("…или тестовый пример", ["", *EXAMPLES])
    return (example, (SYNTHETIC_DIR / example).read_bytes()) if example else None


def saved_mapping(name: str) -> dict[str, str]:
    # Готовая разметка есть только у тестовых примеров (эталоны в data/synthetic).
    # Разметку своих файлов не сохраняем: даже названия колонок - сведения о бизнесе
    if name not in EXAMPLES:
        return {}
    return json.loads(mapping_path(SYNTHETIC_DIR / name).read_text(encoding="utf-8"))


def ask_mapping(name: str, table: pd.DataFrame) -> dict[str, str] | None:
    # Роль каждой колонки - выпадающим списком. Форма: роли применяются по кнопке,
    # а не после каждого выбора
    saved = saved_mapping(name)
    with st.sidebar.expander("Разметка колонок", expanded=not saved):
        with st.form(f"mapping:{name}"):
            mapping = {}
            for column in table.columns:
                examples = ", ".join(map(str, table[column].dropna().head(EXAMPLES_SHOWN)))
                role = saved.get(column, ROLE_IGNORE)
                mapping[column] = st.selectbox(
                    column,
                    list(ROLE_LABELS),
                    index=list(ROLE_LABELS).index(role) if role in ROLE_LABELS else 0,
                    format_func=ROLE_LABELS.get,
                    help=f"Примеры: {examples}",
                )
            if st.form_submit_button("Готово"):
                st.session_state[f"applied:{name}"] = mapping
    # Применённая разметка: по кнопке "Готово" или эталон примера.
    # Имя в памяти - не как у формы ("mapping:..."): имя формы Streamlit занимает сам
    return st.session_state.get(f"applied:{name}") or saved or None


def ask_settings(suggested: list[str]) -> tuple[list[str], str, str]:
    # Служебные строки (программа предлагает, человек выбирает), валюта, страна праздников
    st.sidebar.subheader("Настройки")
    exclude = st.sidebar.multiselect(
        "Не учитывать (похоже на служебные строки)",
        suggested,
        help="Доставка, комиссии... Среди них бывают и настоящие товары - решать вам",
    )
    currency = st.sidebar.text_input("Валюта", CURRENCY) or CURRENCY
    country = st.sidebar.selectbox(
        "Праздники для прогноза",
        list(COUNTRY_NAMES),
        index=list(COUNTRY_NAMES).index(COUNTRY),
        format_func=lambda code: f"{code} - {COUNTRY_NAMES[code]}",
    )
    return exclude, currency, country


# ---------- вкладки ----------


def overview_tab(events: pd.DataFrame, report: dict, currency: str) -> None:
    try:
        month = last_full_month_vs_previous(events)
        columns = st.columns(3)
        columns[0].metric(
            f"Выручка: {month['месяц']}",
            f"{money(month['стало'])} {currency}",
            f"{month['изменение_%']}% к прошлому месяцу"
            if month["изменение_%"] is not None
            else None,
        )
        columns[1].metric(
            "В среднем в день",
            f"{money(month['в_день_стало'])} {currency}",
            f"{month['изменение_в_день_%']}%" if month["изменение_в_день_%"] is not None else None,
        )
        columns[2].metric(
            f"Выручка: {month['прошлый_месяц']}", f"{money(month['было'])} {currency}"
        )
    except ValueError as error:
        st.info(str(error))

    monthly = by_period(events, "месяц", full_periods_only=True)
    st.pyplot(line_chart(monthly, "Выручка по месяцам", currency))
    skipped = incomplete_periods(events)
    if skipped:
        st.caption(f"Неполные месяцы не показаны: {', '.join(skipped)}")
    with st.expander("Как подготовлены данные"):
        st.json(report)


def top_tab(events: pd.DataFrame, currency: str) -> None:
    numeric = numeric_fields(events)
    fields = [f for f in available_fields(events) if f not in numeric and f not in NOT_GROUPED]
    left, middle, right = st.columns(3)
    by = left.selectbox("По чему", fields, format_func=lambda field: FIELDS.get(field, field))
    top = middle.slider("Сколько показать", 3, 30, 10)
    worst = right.toggle("Худшие вместо лучших")
    table = breakdown(events, by=by, top=top, worst=worst)
    title = f"{'Худшие' if worst else 'Топ'}: {FIELDS.get(by, by)}"
    st.pyplot(bar_chart(table, title, currency))
    st.dataframe(table)


def item_tab(events: pd.DataFrame, currency: str) -> None:
    left, right = st.columns([3, 1])
    query = left.text_input("Название, его часть или артикул")
    all_matches = right.toggle("Все подходящие вместе")
    if not query:
        return
    try:
        detail = item_detail(events, query, all_matches=all_matches)
    except ValueError as error:  # "не найдено" или "подходит несколько - уточните"
        st.warning(str(error))
        return
    st.subheader(detail["товар"])
    columns = st.columns(3)
    columns[0].metric("Выручка", f"{money(detail.get('выручка', 0))} {currency}")
    columns[1].metric("Доля выручки", f"{detail.get('доля_выручки_%', 0)}%")
    columns[2].metric("Количество", money(detail.get("количество", 0)))
    st.caption(
        f"Продажи с {detail['первая_продажа']:%d.%m.%Y} по {detail['последняя_продажа']:%d.%m.%Y}"
    )
    if not detail["динамика"].empty:
        st.pyplot(line_chart(detail["динамика"], f"{detail['товар']}: выручка", currency))
    if len(detail["позиции"]) > 1:
        st.write("Позиции:", ", ".join(detail["позиции"]))


def compare_tab(events: pd.DataFrame, currency: str) -> None:
    start, end = events["date"].min().date(), events["date"].max().date()
    left, right = st.columns(2)
    # Календарь выбора периода: пока выбрана только первая дата - ждём вторую
    first = left.date_input("Первый период", (start, end), min_value=start, max_value=end)
    second = right.date_input("Второй период", (start, end), min_value=start, max_value=end)
    if len(first) < 2 or len(second) < 2:
        st.info("Выберите в календаре начало и конец обоих периодов")
        return
    result = compare_periods(
        events,
        tuple(f"{day:%Y-%m-%d}" for day in first),
        tuple(f"{day:%Y-%m-%d}" for day in second),
    )
    columns = st.columns(3)
    columns[0].metric("Было", f"{money(result['было'])} {currency}")
    columns[1].metric("Стало", f"{money(result['стало'])} {currency}")
    percent = result["изменение_%"]
    columns[2].metric(
        "Изменение",
        f"{money(result['изменение'])} {currency}",
        f"{percent}%" if percent is not None else None,
    )
    for warning in result["предупреждения"]:
        st.warning(warning)


def forecast_tab(settings: tuple, events: pd.DataFrame, country: str, currency: str) -> None:
    # Прогноз считается несколько секунд (на большом файле - минуту), поэтому - по кнопке.
    # settings - разметка и исключения: поменялись - прогноз считается заново
    if st.button("Посчитать прогноз", type="primary"):
        st.session_state["forecast"] = True
    if not st.session_state.get("forecast"):
        st.caption("Программа проверит модели на прошлом и сама выберет, на сколько дней вперёд")
        return
    result = remembered(
        ("прогноз", *settings, country, currency),
        lambda: make_forecast(events, country=country, currency=currency),
        "Проверяю модели на прошлом и подбираю горизонт...",
    )
    st.write(result["сообщение"])
    if result["ступенька"] != STEP_FORECAST:
        return
    chart_title = f"Прогноз на {result['горизонт_дней']} дн. ({result['модель']})"
    st.pyplot(forecast_chart(to_daily(events), result["прогноз"], chart_title, currency=currency))
    st.markdown("**Почему такая точность:**")
    for reason in result["точность"]["причины"]:
        st.markdown(f"- {reason}")


# ---------- страница ----------


def main() -> None:
    st.set_page_config(page_title="AI-аналитик", layout="wide")
    st.title("AI-аналитик для малого бизнеса")

    file = choose_file()
    if file is None:
        st.info("Загрузите Excel или CSV с продажами слева - или выберите тестовый пример")
        return
    name, data = file
    # Отпечаток содержимого: тот же файл после перезагрузки страницы - тот же отпечаток
    forget_previous_file(f"{name}:{hashlib.sha256(data).hexdigest()}")
    try:
        table = remembered(
            ("таблица",),
            lambda: read_table(name, data),
            "Читаю файл (большой - до минуты, но только один раз)...",
        )
    except ValueError as error:  # "не удалось определить кодировку"...
        st.error(f"Не получилось прочитать файл: {error}")
        return
    mapping = ask_mapping(name, table)
    if mapping is None:
        st.info("Укажите слева, что значит каждая колонка, и нажмите «Готово»")
        return
    mapping_key = tuple(mapping.items())  # словарь нельзя сделать ключом памяти, кортеж - можно
    try:
        events, report = remembered(
            ("события", mapping_key), lambda: prepare_table(table, mapping), "Готовлю данные..."
        )
    except ValueError as error:  # "нет колонки с датой", "одна роль у двух колонок"...
        st.error(f"Не получилось подготовить данные: {error}")
        return
    suggested = remembered(
        ("служебные", mapping_key), lambda: suggest_exclusions(events), "Ищу служебные строки..."
    )
    if "amount" not in available_fields(events):
        st.error("Нужна колонка с суммой - или цена и количество, тогда сумма посчитается сама")
        return

    exclude, currency, country = ask_settings(suggested)
    if exclude:
        events, excluded = exclude_objects(events, exclude)
        report = {**report, **excluded}

    tabs = st.tabs(["Обзор", "Топ", "Товар", "Сравнение периодов", "Прогноз"])
    with tabs[0]:
        overview_tab(events, report, currency)
    with tabs[1]:
        top_tab(events, currency)
    with tabs[2]:
        item_tab(events, currency)
    with tabs[3]:
        compare_tab(events, currency)
    with tabs[4]:
        forecast_tab((mapping_key, tuple(exclude)), events, country, currency)


if __name__ == "__main__":  # Streamlit запускает файл именно так
    main()
