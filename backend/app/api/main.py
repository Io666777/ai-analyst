"""Приложение API: точка входа для uvicorn. Собирает ручки из routes/ вместе."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import files, session, setup
from app.config import FRONTEND_URL

API_PREFIX = "/api"  # все ручки под /api - не путаются с адресами фронта

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

service = APIRouter(tags=["служебное"])


@service.get("/health", summary="Сервер жив")
def health() -> dict[str, str]:
    """По этой ручке фронт и Render проверяют, что API работает."""
    return {"status": "ok"}


for router in (service, files.router, setup.router, session.router):
    app.include_router(router, prefix=API_PREFIX)
