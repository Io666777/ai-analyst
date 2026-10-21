"""Боковая панель: выбор файла, разметка колонок, настройки."""

import json

import pandas as pd
import streamlit as st

from app.config import CURRENCY, SYNTHETIC_DIR
from app.forecast import COUNTRY, COUNTRY_NAMES
from app.loader import EXCEL_SUFFIXES
from app.model import ROLE_CHOICES, ROLE_IGNORE

EXAMPLES = ["shop.xlsx", "cafe.csv", "salon.xlsx"]  # тестовые бизнесы из data/synthetic
EXAMPLES_SHOWN = 3  # сколько примеров значений показывать при разметке колонки
ROLE_LABELS = {ROLE_IGNORE: "— не нужна —", **dict(ROLE_CHOICES)}


def choose_file() -> tuple[str, bytes] | None:
    # Свой файл или тестовый пример -> (имя файла, содержимое)
    uploaded = st.sidebar.file_uploader("Файл с продажами", type=["csv", *EXCEL_SUFFIXES])
    st.sidebar.caption("Файл не сохраняется: он в памяти, пока открыта вкладка")
    if uploaded is not None:
        return uploaded.name, uploaded.getvalue()
    example = st.sidebar.selectbox("…или тестовый пример", ["", *EXAMPLES])
    return (example, (SYNTHETIC_DIR / example).read_bytes()) if example else None


def saved_mapping(name: str) -> dict[str, str]:
    # Готовая разметка есть только у тестовых примеров (эталоны *.json в data/synthetic).
    # Разметку своих файлов не сохраняем: даже названия колонок - сведения о бизнесе
    if name not in EXAMPLES:
        return {}
    etalon = (SYNTHETIC_DIR / name).with_suffix(".json")
    return json.loads(etalon.read_text(encoding="utf-8"))


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
                    key=f"role:{name}:{column}",  # свой ключ - списки не спутаются
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
