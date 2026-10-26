// Прогноз: запуск долгого расчёта и счётчик секунд, пока он идёт
import type { Ref } from 'vue';
import { onBeforeUnmount, ref } from 'vue';
import { useSessionState } from '~/entities/session';
import { type Forecast, toApiError } from '~/shared/api';
import { useRequest } from '~/shared/lib';
import { fetchForecast } from '../api/forecast-api';

const SECOND_MS = 1000;

export interface UseForecast {
  data: Ref<Forecast | null>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  /** Сколько секунд идёт расчёт - видно, что программа не зависла. */
  elapsed: Ref<number>;
  /** Посчитать прогноз. */
  calculate: () => Promise<void>;
}

/**
 * Прогноз по кнопке. Сервер запоминает результат: повторное нажатие - мгновенно.
 * @returns {UseForecast} ответ, состояние и запуск.
 */
export function useForecast(): UseForecast {
  // Посчитанный прогноз переживает переключение вкладок: считать заново - до минуты
  const { data, isLoading, error, run } = useRequest(
    fetchForecast,
    err => toApiError(err).message,
    useSessionState<Forecast | null>('forecast-data', () => null),
  );
  const elapsed = ref(0);
  let timer: ReturnType<typeof setInterval> | undefined;

  /** Запустить расчёт и считать секунды до ответа. */
  async function calculate(): Promise<void> {
    elapsed.value = 0;
    clearInterval(timer);
    timer = setInterval(() => {
      elapsed.value += 1;
    }, SECOND_MS);
    try {
      await run();
    } finally {
      clearInterval(timer);
    }
  }

  onBeforeUnmount(() => clearInterval(timer));

  return { data, isLoading, error, elapsed, calculate };
}
