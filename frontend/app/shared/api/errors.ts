import { FetchError } from 'ofetch';
import { API_ERROR_CODES, ERROR_CODE_HEADER, HTTP_STATUS } from '~/shared/config';

/** Тексты ошибок, которые сервер не прислал сам. */
export const API_ERROR_MESSAGES = {
  network: 'Сервер не отвечает - проверьте подключение к интернету и попробуйте ещё раз',
  validation: 'Проверьте введённые данные',
  server: 'Ошибка на сервере - попробуйте ещё раз',
  unknown: 'Что-то пошло не так - попробуйте ещё раз',
} as const;

/**
 * Ошибка запроса к API с понятным человеку текстом (message) - его можно показать как есть.
 */
export class ApiError extends Error {
  /** Код ответа: 404, 409... null - ответа не было (сервер недоступен). */
  readonly status: number | null;
  /** Машинный код ошибки из заголовка X-Error-Code. */
  readonly code: string | null;

  /**
   * @param {string} message - текст для человека.
   * @param {number | null} status - код ответа.
   * @param {string | null} code - машинный код ошибки.
   */
  constructor(message: string, status: number | null, code: string | null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }

  /** Сессия устарела или удалена: нужно загрузить файл заново. */
  get isSessionExpired(): boolean {
    return this.code === API_ERROR_CODES.sessionExpired;
  }
}

/**
 * Текст ошибки для человека по ответу сервера.
 * @param {number} status - код ответа.
 * @param {unknown} detail - поле detail из ответа FastAPI: строка или список ошибок проверки.
 * @returns {string} текст ошибки.
 */
function messageFor(status: number, detail: unknown): string {
  if (status >= HTTP_STATUS.serverError) return API_ERROR_MESSAGES.server;
  // 422: FastAPI присылает список ошибок проверки на английском - показываем общий текст
  if (status === HTTP_STATUS.validation) return API_ERROR_MESSAGES.validation;
  return typeof detail === 'string' ? detail : API_ERROR_MESSAGES.unknown;
}

/**
 * Любая ошибка запроса → ApiError с понятным текстом.
 * @param {unknown} error - что выбросил запрос.
 * @returns {ApiError} ошибка для показа человеку.
 */
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (!(error instanceof FetchError) || !error.response) {
    return new ApiError(API_ERROR_MESSAGES.network, null, null); // ответа не было вовсе
  }
  const { status, headers } = error.response;
  return new ApiError(
    messageFor(status, error.data?.detail),
    status,
    headers.get(ERROR_CODE_HEADER),
  );
}
