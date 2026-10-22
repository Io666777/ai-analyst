"""API для фронта: FastAPI вызывает готовые функции из data, analytics, forecast.

Запуск из папки backend:
    venv\\Scripts\\python.exe -m uvicorn app.api.main:app --reload

Документация (Swagger) с возможностью вызвать любую ручку - http://localhost:8000/api/docs,
то же в виде ReDoc - /api/redoc, описание OpenAPI для генерации типов фронта - /api/openapi.json

Разложено по частям:
    main - приложение: подключение ручек, разрешение запросов от фронта (CORS)

Здесь только приём запросов и выдача ответов - все расчёты в готовых функциях из app/.
"""
