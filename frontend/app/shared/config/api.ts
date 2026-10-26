/** Префикс всех ручек API. Сам адрес сервера - в runtimeConfig.public.apiUrl (nuxt.config.ts). */
export const API_PREFIX = '/api';

/** Заголовок, в котором фронт присылает номер сессии. */
export const SESSION_HEADER = 'X-Session-Id';

/** Заголовок ответа с машинным кодом ошибки (backend/app/api/dependencies.py). */
export const ERROR_CODE_HEADER = 'X-Error-Code';

/** Машинные коды ошибок API: по ним фронт реагирует, не сравнивая тексты. */
export const API_ERROR_CODES = {
  sessionExpired: 'session-expired',
} as const;

/** Адреса ручек API без префикса. Описание каждой - в Swagger: /api/docs. */
export const API_ENDPOINTS = {
  health: '/health',
  options: '/options',
  files: '/files',
  session: '/session',
  mapping: '/session/mapping',
  settings: '/session/settings',
  overview: '/analysis/overview',
  daily: '/analysis/daily',
  top: '/analysis/top',
  items: '/analysis/items',
  catalog: '/analysis/catalog',
  item: '/analysis/item',
  itemDays: '/analysis/item/days',
  compare: '/analysis/compare',
  forecast: '/analysis/forecast',
} as const;

// Ограничения - те же, что на сервере. Проверяем до отправки, чтобы не гонять файл по сети зря

/** Максимальный размер загружаемого файла, МБ. */
export const MAX_UPLOAD_MB = 20;

/** Форматы файлов, которые принимает сервер. */
export const ALLOWED_FILE_EXTENSIONS = ['.csv', '.xlsx', '.xls'] as const;

/** Сколько строк можно запросить в топе. */
export const TOP_LIMITS = { min: 1, max: 50, default: 10 } as const;

/** Коды ответа сервера, на которые фронт реагирует по-особому. */
export const HTTP_STATUS = {
  noContent: 204,
  badRequest: 400,
  notFound: 404, // сессия устарела или товар не найден
  conflict: 409, // сначала нужно разметить колонки
  tooLarge: 413,
  validation: 422,
  serverError: 500, // и всё выше - ошибка на стороне сервера
} as const;
