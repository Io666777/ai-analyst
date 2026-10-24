// Запросы карточки товара: всё о товаре и товар по дням периода
import { api, type ItemDays, type ItemDetail } from '~/shared/api';
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

/**
 * Товар по дням периода: выручка, штуки, кто продавал.
 * @param {object} request - что и за какой период.
 * @param {string} request.query - название товара, а для all - запрос.
 * @param {boolean} request.all - все подходящие товары вместе.
 * @param {string} request.dateFrom - с какого дня: "2026-09-01".
 * @param {string} request.dateTo - по какой день, включительно.
 * @returns {Promise<ItemDays>} дни периода и итоги.
 */
export function fetchItemDays(request: {
  query: string;
  all: boolean;
  dateFrom: string;
  dateTo: string;
}): Promise<ItemDays> {
  return api.get<ItemDays>(API_ENDPOINTS.itemDays, {
    q: request.query,
    all: request.all || undefined,
    date_from: request.dateFrom,
    date_to: request.dateTo,
  });
}
