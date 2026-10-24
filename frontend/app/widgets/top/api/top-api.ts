// Запрос топа: лучшие или худшие по выбранному полю
import { api, type Top } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';

export interface TopParams {
  /** Поле: object, category или дополнительное («Бренд»). Не задано - сервер возьмёт товар. */
  by?: string;
  /** Сколько строк. */
  top: number;
  /** true - худшие вместо лучших. */
  worst: boolean;
}

/**
 * Топ по выбранному полю с долей от всей выручки.
 * @param {TopParams} params - поле, сколько строк, лучшие или худшие.
 * @returns {Promise<Top>} строки топа и поля, по которым его можно построить.
 */
export function fetchTop(params: TopParams): Promise<Top> {
  return api.get<Top>(API_ENDPOINTS.top, { ...params });
}
