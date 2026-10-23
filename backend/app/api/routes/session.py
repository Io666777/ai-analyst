"""Ручки сессии: удалить свои данные с сервера."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import SESSION_EXPIRED, SessionId
from app.api.sessions import SessionNotFoundError, store

router = APIRouter(tags=["сессия"])


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить мои данные")
def forget_session(session_id: SessionId) -> None:
    """Сессия и всё в ней (таблица, разметка, результаты) сразу исчезают из памяти сервера."""
    try:
        store.delete(session_id)
    except SessionNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, SESSION_EXPIRED) from None
