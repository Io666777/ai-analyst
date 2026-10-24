// Поиск товара: подсказки при вводе
import { api, type ItemsFound } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';

/**
 * Товары, похожие на запрос: точное название, артикул, часть названия.
 * @param {string} query - что ввели.
 * @returns {Promise<ItemsFound>} до 20 подсказок и сколько нашлось всего.
 */
export function searchItems(query: string): Promise<ItemsFound> {
  return api.get<ItemsFound>(API_ENDPOINTS.items, { q: query });
}
