// Публичный вход сегмента shared/api: снаружи импортируем только отсюда
export { api, configureApiClient, type ApiClientOptions, type ApiQuery } from './client';
export { API_ERROR_MESSAGES, ApiError, toApiError } from './errors';
export type * from './types';
