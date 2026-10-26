// Фильтр каталога товаров на каждую букву - прямо в браузере, без запроса к серверу.
// Порядок - как у поиска на сервере (backend/app/analytics/items.py, match_rank):
// сначала названия, которые начинаются с запроса, потом - где с него начинается слово,
// потом - совпадение внутри слова. Внутри группы - прежний порядок (по выручке)

/** Насколько рано совпадение: 0 - начало названия, 1 - начало слова, 2 - внутри слова. */
function matchRank(name: string, text: string): number {
  if (name.startsWith(text)) return 0;
  return name.split(/\s+/).some(word => word.startsWith(text)) ? 1 : 2;
}

/**
 * Товары, в названии которых есть запрос, - самые подходящие первыми.
 * @param {readonly T[]} items - товары каталога (по выручке).
 * @param {string} query - что ввели; пусто - весь каталог как есть.
 * @returns {T[]} подходящие товары.
 */
export function filterItems<T extends { name: string }>(items: readonly T[], query: string): T[] {
  const text = query.trim().toLowerCase();
  if (!text) return [...items];
  return items
    .map((item, order) => ({ item, order, name: item.name.toLowerCase() }))
    .filter(({ name }) => name.includes(text))
    .sort((a, b) => matchRank(a.name, text) - matchRank(b.name, text) || a.order - b.order)
    .map(({ item }) => item);
}
