"""Приложение API: точка входа для uvicorn."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL

API_PREFIX = "/api"  # все ручки под /api - не путаются с адресами фронта

# Группы ручек в Swagger - по разделам
TAG_SERVICE = "служебное"

app = FastAPI(
    title="AI-аналитик для малого бизнеса",
    description="Загрузка выгрузки продаж, аналитика и прогноз. Данные хранятся только в памяти "
    "сервера на время сессии и никуда не записываются.",
    version="0.1.0",
    # Swagger, ReDoc и описание OpenAPI - тоже под /api, вместе с ручками
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# Браузер по умолчанию не пускает страницу с одного адреса (фронт) к другому (API).
# Разрешаем это только нашему фронту
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix=API_PREFIX)


@router.get("/health", tags=[TAG_SERVICE], summary="Сервер жив")
def health() -> dict[str, str]:
    """По этой ручке фронт и Render проверяют, что API работает."""
    return {"status": "ok"}


app.include_router(router)
