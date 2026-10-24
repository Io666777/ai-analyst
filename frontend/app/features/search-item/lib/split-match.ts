// Название, разрезанное вокруг совпадения: «Сухарики» на «су» → «» + «Су» + «харики».
// В подсказках совпавшая часть выделяется - видно, почему товар подошёл

export interface MatchParts {
  before: string;
  match: string;
  after: string;
}

/**
 * Где в названии совпадение: в начале слова, если есть, иначе где угодно -
 * как сервер выбирает порядок подсказок (backend/app/analytics/items.py, match_rank).
 * @param {string} name - название товара.
 * @param {string} query - что ввели.
 * @returns {MatchParts} части; совпадения нет - всё название в before.
 */
export function splitMatch(name: string, query: string): MatchParts {
  const text = query.trim().toLowerCase();
  const lower = name.toLowerCase();
  if (!text) return { before: name, match: '', after: '' };

  const wordStart = [...lower.matchAll(/\S+/g)].find(word => word[0].startsWith(text))?.index;
  const index = wordStart ?? lower.indexOf(text);
  if (index < 0) return { before: name, match: '', after: '' };

  return {
    before: name.slice(0, index),
    match: name.slice(index, index + text.length),
    after: name.slice(index + text.length),
  };
}
