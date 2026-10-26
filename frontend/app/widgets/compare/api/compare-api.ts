// Запрос сравнения двух периодов
import { api, type Comparison } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';
import type { PeriodPair } from '../lib/presets';

/**
 * Было и стало: итоги, изменение, среднее за день, предупреждения.
 * @param {PeriodPair} pair - два периода.
 * @returns {Promise<Comparison>} сравнение.
 */
export function fetchComparison(pair: PeriodPair): Promise<Comparison> {
  return api.get<Comparison>(API_ENDPOINTS.compare, {
    first_from: pair.first.from,
    first_to: pair.first.to,
    second_from: pair.second.from,
    second_to: pair.second.to,
  });
}
