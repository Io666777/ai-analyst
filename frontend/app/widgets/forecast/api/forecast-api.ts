// Запрос прогноза: долгий расчёт на сервере, повторный запрос - из памяти сессии
import { api, type Forecast } from '~/shared/api';
import { API_ENDPOINTS } from '~/shared/config';

/**
 * Посчитать прогноз (или получить уже посчитанный).
 * @returns {Promise<Forecast>} ступенька, сообщение, точность, точки для графика.
 */
export function fetchForecast(): Promise<Forecast> {
  return api.post<Forecast>(API_ENDPOINTS.forecast);
}
