// Запрос обзора: как прошёл месяц и выручка по месяцам
import { api, type Overview } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';

/**
 * Обзор продаж с учётом текущих настроек сессии.
 * @returns {Promise<Overview>} итоги, последний месяц и выручка по месяцам.
 */
export function fetchOverview(): Promise<Overview> {
  return api.get<Overview>(API_ENDPOINTS.overview);
}
