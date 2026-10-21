"""Сама страница: файл -> разметка -> данные -> настройки -> вкладки.

Запуск из папки backend:
    venv\\Scripts\\python.exe -m streamlit run app/web/page.py
"""

import hashlib

import streamlit as st

from app.model import available_fields, exclude_objects, suggest_exclusions
from app.pipeline import prepare_table
from app.web.memory import forget_previous_file, read_table, remembered
from app.web.sidebar import ask_mapping, ask_settings, choose_file
from app.web.tabs import compare_tab, forecast_tab, item_tab, overview_tab, top_tab


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
    if "amount" not in available_fields(events):
        st.error("Нужна колонка с суммой - или цена и количество, тогда сумма посчитается сама")
        return
    suggested = remembered(
        ("служебные", mapping_key), lambda: suggest_exclusions(events), "Ищу служебные строки..."
    )

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
