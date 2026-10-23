"""Сессии в памяти: данные пользователя живут только на время работы и никуда не пишутся.

Пользователь загрузил файл -> сессия со случайным номером. Фронт присылает номер с каждым
запросом (заголовок X-Session-Id). Сессия забывается через полчаса без запросов или по кнопке
"удалить мои данные". На диск ничего не записывается.
"""

import secrets
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.config import CURRENCY
from app.forecast import COUNTRY

SESSION_TTL_SECONDS = 30 * 60  # через полчаса без запросов сессия забывается
MAX_SESSIONS = 20  # больше одновременно не держим: на Render всего 512 МБ памяти
SESSION_ID_BYTES = 24  # длина случайного номера: 24 байта -> 32 символа, не угадать


@dataclass
class Session:
    # Всё, что сервер помнит об одном пользователе
    file_name: str
    table: pd.DataFrame  # таблица из файла, как есть
    mapping: dict[str, str] | None = None  # роли колонок - после разметки
    events: pd.DataFrame | None = None  # подготовленные события - после разметки
    report: dict | None = None  # отчёт о подготовке
    exclude: list[str] = field(default_factory=list)  # служебные строки, которые не учитывать
    currency: str = CURRENCY
    country: str = COUNTRY
    cache: dict[Any, Any] = field(default_factory=dict)  # посчитанное: прогноз и т.п.
    last_used: float = 0.0  # когда к сессии обращались в последний раз


class SessionNotFoundError(Exception):
    # Номера нет: устарел, удалён или выдуман
    pass


class SessionStore:
    def __init__(
        self,
        ttl: float = SESSION_TTL_SECONDS,
        max_sessions: int = MAX_SESSIONS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        # clock - откуда брать время. В тестах подставляем свои часы и "переводим стрелки"
        self.ttl = ttl
        self.max_sessions = max_sessions
        self.clock = clock
        # Порядок - по последнему использованию: в начале самые давние
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        # Запросы обрабатываются параллельно - словарь меняет только один поток за раз
        self._lock = threading.Lock()

    def create(self, file_name: str, table: pd.DataFrame) -> str:
        # Новая сессия -> её номер. Нет места - вытесняем самую давно не использованную
        with self._lock:
            self._forget_expired()
            while len(self._sessions) >= self.max_sessions:
                self._sessions.popitem(last=False)
            session_id = secrets.token_urlsafe(SESSION_ID_BYTES)
            self._sessions[session_id] = Session(file_name, table, last_used=self.clock())
            return session_id

    def get(self, session_id: str) -> Session:
        # Сессия по номеру. Обращение продлевает ей жизнь ещё на полчаса
        with self._lock:
            self._forget_expired()
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            session.last_used = self.clock()
            self._sessions.move_to_end(session_id)  # теперь она самая свежая
            return session

    def delete(self, session_id: str) -> None:
        # "Удалить мои данные": сессия и всё в ней исчезают сразу
        with self._lock:
            if self._sessions.pop(session_id, None) is None:
                raise SessionNotFoundError(session_id)

    def __len__(self) -> int:
        return len(self._sessions)

    def _forget_expired(self) -> None:
        # Забываем сессии, к которым не обращались дольше ttl. Вызывается под блокировкой.
        # Сессии упорядочены по последнему использованию - достаточно смотреть с начала
        now = self.clock()
        while self._sessions:
            oldest = next(iter(self._sessions.values()))
            if now - oldest.last_used <= self.ttl:
                break
            self._sessions.popitem(last=False)


store = SessionStore()  # одно хранилище на весь сервер
