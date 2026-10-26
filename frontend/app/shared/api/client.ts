// Клиент запросов к API. Ничего не знает о сессии и страницах: номер сессии и что делать,
// когда она устарела, ему передаёт слой app при запуске (configureApiClient).
// Так shared не зависит от слоёв выше - импорты идут только вниз
import { ofetch } from 'ofetch';
import { API_PREFIX, SESSION_HEADER } from '~/shared/config';
import { toApiError } from './errors';

export interface ApiClientOptions {
  /** Адрес сервера API: "http://localhost:8000". */
  baseUrl: string;
  /** Номер текущей сессии; null - сессии ещё нет. */
  getSessionId: () => string | null;
  /** Что делать, когда сервер сообщил «сессия устарела». */
  onSessionExpired: () => void;
}

/** Параметры адреса: ?q=пиво&top=10. undefined не попадают в адрес. */
export type ApiQuery = Record<string, string | number | boolean | undefined>;

const HTTP_METHODS = {
  get: 'GET',
  post: 'POST',
  put: 'PUT',
  delete: 'DELETE',
} as const;

type HttpMethod = (typeof HTTP_METHODS)[keyof typeof HTTP_METHODS];

const UPLOAD_FIELD = 'file'; // имя поля с файлом - как в ручке POST /api/files

let clientOptions: ApiClientOptions | null = null;

/**
 * Настраивает клиент. Вызывается один раз при запуске приложения (слой app).
 * @param {ApiClientOptions} options - адрес API, номер сессии, реакция на устаревшую сессию.
 */
export function configureApiClient(options: ApiClientOptions): void {
  clientOptions = options;
}

/**
 * Настройки клиента; без них запрос не отправить.
 * @returns {ApiClientOptions} настройки.
 */
function requireOptions(): ApiClientOptions {
  if (!clientOptions) {
    throw new Error('API-клиент не настроен: вызовите configureApiClient при запуске приложения');
  }
  return clientOptions;
}

/**
 * Запрос к API: адрес сервера, номер сессии, понятные ошибки.
 * @param {string} path - адрес ручки без префикса: "/analysis/top".
 * @param {object} init - метод, параметры адреса и тело запроса.
 * @param {HttpMethod} init.method - метод запроса.
 * @param {ApiQuery} [init.query] - параметры адреса.
 * @param {unknown} [init.body] - тело: объект (уйдёт как JSON) или FormData (файл).
 * @returns {Promise<T>} ответ сервера.
 * @throws {ApiError} ошибка с текстом для человека.
 */
async function request<T>(
  path: string,
  init: { method: HttpMethod; query?: ApiQuery; body?: Record<string, unknown> | FormData },
): Promise<T> {
  const { baseUrl, getSessionId, onSessionExpired } = requireOptions();
  const sessionId = getSessionId();
  try {
    return await ofetch<T>(`${API_PREFIX}${path}`, {
      baseURL: baseUrl,
      method: init.method,
      query: init.query,
      body: init.body,
      headers: sessionId ? { [SESSION_HEADER]: sessionId } : undefined,
    });
  } catch (error) {
    const apiError = toApiError(error);
    if (apiError.isSessionExpired) onSessionExpired();
    throw apiError;
  }
}

/** Запросы к API. Ошибки - ApiError с текстом, который можно показать как есть. */
export const api = {
  /**
   * Получить данные.
   * @param {string} path - адрес ручки.
   * @param {ApiQuery} [query] - параметры адреса.
   * @returns {Promise<T>} ответ.
   */
  get: <T>(path: string, query?: ApiQuery): Promise<T> =>
    request<T>(path, { method: HTTP_METHODS.get, query }),

  /**
   * Отправить данные или запустить расчёт.
   * @param {string} path - адрес ручки.
   * @param {Record<string, unknown>} [body] - тело запроса.
   * @returns {Promise<T>} ответ.
   */
  post: <T>(path: string, body?: Record<string, unknown>): Promise<T> =>
    request<T>(path, { method: HTTP_METHODS.post, body }),

  /**
   * Заменить данные (разметка, настройки).
   * @param {string} path - адрес ручки.
   * @param {Record<string, unknown>} body - тело запроса.
   * @returns {Promise<T>} ответ.
   */
  put: <T>(path: string, body: Record<string, unknown>): Promise<T> =>
    request<T>(path, { method: HTTP_METHODS.put, body }),

  /**
   * Удалить (данные сессии).
   * @param {string} path - адрес ручки.
   * @returns {Promise<void>} ничего - сервер отвечает 204.
   */
  delete: async (path: string): Promise<void> => {
    await request<unknown>(path, { method: HTTP_METHODS.delete });
  },

  /**
   * Загрузить файл - как форма с полем file.
   * @param {string} path - адрес ручки.
   * @param {File} file - файл пользователя.
   * @returns {Promise<T>} ответ.
   */
  upload: <T>(path: string, file: File): Promise<T> => {
    const form = new FormData();
    form.append(UPLOAD_FIELD, file);
    return request<T>(path, { method: HTTP_METHODS.post, body: form });
  },
};
