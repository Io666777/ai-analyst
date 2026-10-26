// Запрос топа: лучшие или худшие по выбранному полю за период
import { api, type Top } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';

export interface TopRequest {
  /** Поле: object, category или дополнительное («Бренд»). Не задано - сервер возьмёт товар. */
  by?: string;
  /** Сколько строк. */
  top: number;
  /** true - худшие вместо лучших. */
  worst: boolean;
  /** С какого дня ("2026-09-01"); пусто - с начала данных. */
  dateFrom: string;
  /** По какой день, включительно; пусто - до конца данных. */
  dateTo: string;
}

/**
 * Топ по выбранному полю за период с долей от всей выручки периода.
 * @param {TopRequest} request - поле, сколько строк, лучшие или худшие, период.
 * @returns {Promise<Top>} строки топа, итог периода и поля, по которым можно строить топ.
 */
export function fetchTop(request: TopRequest): Promise<Top> {
  return api.get<Top>(API_ENDPOINTS.top, {
    by: request.by,
    top: request.top,
    worst: request.worst,
    date_from: request.dateFrom || undefined,
    date_to: request.dateTo || undefined,
  });
}
