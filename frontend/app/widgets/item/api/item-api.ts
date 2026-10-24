// Запрос карточки товара
import { api, type ItemDetail } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';

/**
 * Всё о товаре: выручка, доля, количество, даты продаж, динамика по месяцам.
 * @param {string} query - название товара, а для all - запрос.
 * @param {boolean} all - все подходящие товары вместе.
 * @returns {Promise<ItemDetail>} карточка товара.
 */
export function fetchItem(query: string, all: boolean): Promise<ItemDetail> {
  // all=false не передаём: это и так поведение сервера по умолчанию
  return api.get<ItemDetail>(API_ENDPOINTS.item, { q: query, all: all || undefined });
}
