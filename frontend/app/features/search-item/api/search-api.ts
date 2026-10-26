// Каталог товаров и поиск на сервере (по артикулу и другим признакам)
import { api, type Catalog, type ItemsFound } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';

/**
 * Все товары от самых продаваемых - для списка под поиском.
 * @returns {Promise<Catalog>} товары с выручкой и долей.
 */
export function fetchCatalog(): Promise<Catalog> {
  return api.get<Catalog>(API_ENDPOINTS.catalog);
}

/**
 * Товары, похожие на запрос: точное название, артикул, часть названия.
 * @param {string} query - что ввели.
 * @returns {Promise<ItemsFound>} до 20 подсказок и сколько нашлось всего.
 */
export function searchItems(query: string): Promise<ItemsFound> {
  return api.get<ItemsFound>(API_ENDPOINTS.items, { q: query });
}
