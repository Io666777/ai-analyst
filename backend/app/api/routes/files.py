"""Ручки загрузки: свой файл или тестовый пример -> новая сессия и колонки для разметки."""

import json
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.schemas import ColumnPreview, ExampleInfo, FileOpened
from app.api.sessions import store
from app.config import SYNTHETIC_DIR
from app.data import EXCEL_SUFFIXES, detect_roles, load

router = APIRouter(tags=["загрузка"])

ALLOWED_SUFFIXES = (".csv", *EXCEL_SUFFIXES)
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 МБ: больше - отказ, иначе одной загрузкой забить память
EXAMPLES_SHOWN = 3  # сколько значений колонки показывать при разметке

# Тестовые бизнесы из data/synthetic: файл -> как назвать его пользователю
EXAMPLES = {
    "shop.xlsx": "Магазин: пиво, вода, снеки, хлеб - 2 года",
    "cafe.csv": "Кафе: кофе, десерты, обеды - 2 года",
    "salon.xlsx": "Салон красоты: стрижки, маникюр - 1 год",
}


def read_table(name: str, data: bytes) -> pd.DataFrame:
    # Файл -> таблица первого листа, без сохранения на диск сервера. Функциям чтения нужен путь,
    # поэтому файл кладём во временную папку, читаем, и папка удаляется вместе с ним
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / Path(name).name  # имя без чужих папок: "../x.csv" -> "x.csv"
        path.write_bytes(data)
        sheets = load(path)
    if not sheets:
        raise ValueError("В файле нет данных")
    return next(iter(sheets.values()))


def preview(table: pd.DataFrame) -> list[ColumnPreview]:
    # Колонки с первыми непустыми значениями - для экрана разметки
    return [
        ColumnPreview(
            name=str(column),
            examples=[str(value) for value in table[column].dropna().head(EXAMPLES_SHOWN)],
        )
        for column in table.columns
    ]


def open_table(
    name: str,
    table: pd.DataFrame,
    mapping: dict[str, str],
    confidence: dict[str, float] | None = None,
) -> FileOpened:
    # Таблица -> новая сессия и всё, что нужно фронту для разметки
    session_id = store.create(name, table)
    return FileOpened(
        session_id=session_id,
        file_name=name,
        rows=len(table),
        columns=preview(table),
        mapping=mapping,
        confidence=confidence,
    )


@router.post("/files", summary="Загрузить свой файл")
def upload_file(file: UploadFile) -> FileOpened:
    """Excel или CSV до 20 МБ. Файл читается в память сервера и на диск не записывается."""
    name = file.filename or ""
    if Path(name).suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нужен файл Excel (.xlsx, .xls) или CSV")
    data = file.file.read(MAX_UPLOAD_BYTES + 1)  # на байт больше лимита - чтобы заметить превышение
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"Файл больше {MAX_UPLOAD_BYTES // (1024 * 1024)} МБ",
        )
    try:
        table = read_table(name, data)
    except ValueError as error:  # "не удалось определить кодировку", "в файле нет данных"...
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None
    # Роли угадываем правилами - человек только проверяет, а не размечает всё с нуля
    guesses = detect_roles(table)
    return open_table(
        name,
        table,
        mapping={str(column): role for column, (role, _) in guesses.items()},
        confidence={str(column): confidence for column, (_, confidence) in guesses.items()},
    )


@router.get("/examples", summary="Тестовые примеры")
def list_examples() -> list[ExampleInfo]:
    """Бизнесы с выдуманными данными - чтобы посмотреть программу без своего файла."""
    return [ExampleInfo(name=name, title=title) for name, title in EXAMPLES.items()]


@router.post("/examples/{name}", summary="Открыть тестовый пример")
def open_example(name: str) -> FileOpened:
    """Как загрузка своего файла, но разметка колонок уже готова (эталон из data/synthetic)."""
    if name not in EXAMPLES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Нет примера «{name}»")
    path = SYNTHETIC_DIR / name
    mapping = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    return open_table(name, read_table(name, path.read_bytes()), mapping)
