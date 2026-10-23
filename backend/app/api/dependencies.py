"""Зависимости ручек: то, что FastAPI подставляет в ручку сам, до её вызова.

Ручке нужна сессия -> она объявляет параметр session: CurrentSession, а номер из заголовка,
поиск и ошибка "сессия устарела" - здесь, в одном месте.
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.api.sessions import Session, SessionNotFoundError, store

SESSION_EXPIRED = "Сессия устарела или удалена - загрузите файл заново"


def current_session_id(
    x_session_id: Annotated[
        str, Header(description="Номер сессии, который вернула загрузка файла")
    ],
) -> str:
    # Номер сессии из заголовка X-Session-Id (FastAPI сам переводит x_session_id в X-Session-Id)
    return x_session_id


def current_session(session_id: Annotated[str, Depends(current_session_id)]) -> Session:
    # Сессия по номеру. Нет такой - 404 с понятным текстом: фронт предложит загрузить файл заново
    try:
        return store.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, SESSION_EXPIRED) from None


# Короткие имена для параметров ручек
SessionId = Annotated[str, Depends(current_session_id)]
CurrentSession = Annotated[Session, Depends(current_session)]
