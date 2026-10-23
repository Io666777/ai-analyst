"""Модели ответов API: точная структура JSON для Swagger и для типов TypeScript на фронте."""

from pydantic import BaseModel, Field


class ColumnPreview(BaseModel):
    # Колонка файла: название и несколько значений - по ним человек понимает, что в ней
    name: str = Field(examples=["Дата чека"])
    examples: list[str] = Field(examples=[["01.10.24", "02.10.24", "03.10.24"]])


class FileOpened(BaseModel):
    # Ответ на загрузку файла или открытие примера
    session_id: str = Field(description="Номер сессии: присылать в заголовке X-Session-Id")
    file_name: str = Field(examples=["cafe.csv"])
    rows: int = Field(description="Строк в таблице (первый лист)", examples=[2921])
    columns: list[ColumnPreview]
    mapping: dict[str, str] | None = Field(
        default=None,
        description="Готовая разметка колонок - есть только у тестовых примеров",
        examples=[{"Дата чека": "date", "Выручка, руб": "amount"}],
    )


class ExampleInfo(BaseModel):
    # Тестовый бизнес, который можно открыть без своего файла
    name: str = Field(examples=["cafe.csv"])
    title: str = Field(examples=["Кафе: кофе, десерты, обеды - 2 года"])
