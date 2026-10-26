// Запрос выручки по дням периода
import { api, type Daily } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';

/**
 * Выручка за каждый день периода; дни без продаж - нулём.
 * @param {string} dateFrom - с какого дня: "2026-09-01".
 * @param {string} dateTo - по какой день, включительно.
 * @returns {Promise<Daily>} дни и итог периода.
 */
export function fetchDaily(dateFrom: string, dateTo: string): Promise<Daily> {
  return api.get<Daily>(API_ENDPOINTS.daily, { date_from: dateFrom, date_to: dateTo });
}
