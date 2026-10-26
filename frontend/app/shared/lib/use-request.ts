// Запрос к серверу с состоянием для экрана: данные, «загружается», текст ошибки.
// Один и тот же шаблон у всех разделов анализа - пишем его один раз
import type { Ref } from 'vue';
import { ref, shallowRef } from 'vue';

export interface UseRequest<T, Args extends unknown[]> {
  /** Ответ последнего удачного запроса; null - ещё не было. */
  data: Ref<T | null>;
  isLoading: Ref<boolean>;
  /** Текст ошибки для человека; null - ошибки нет. */
  error: Ref<string | null>;
  /** Выполнить запрос. Ошибку не бросает - кладёт в error. */
  run: (...args: Args) => Promise<T | null>;
}

/**
 * Обёртка над запросом: следит за загрузкой и ошибкой.
 * Ответ на устаревший запрос (пока ждали, отправили новый) не затирает свежий.
 * @param {(...args: Args) => Promise<T>} request - функция запроса.
 * @param {(error: unknown) => string} toMessage - как превратить ошибку в текст.
 * @param {Ref<T | null>} [data] - куда класть ответ: своё хранилище, чтобы ответ пережил
 *   уход со страницы. Не задано - обычная переменная компонента.
 * @returns {UseRequest<T, Args>} состояние и запуск.
 */
export function useRequest<T, Args extends unknown[] = []>(
  request: (...args: Args) => Promise<T>,
  toMessage: (error: unknown) => string,
  data: Ref<T | null> = shallowRef<T | null>(null),
): UseRequest<T, Args> {
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  let lastCall = 0;

  /**
   * Выполняет запрос.
   * @param {Args} args - аргументы запроса.
   * @returns {Promise<T | null>} ответ; null - ошибка или запрос устарел.
   */
  async function run(...args: Args): Promise<T | null> {
    const call = ++lastCall;
    isLoading.value = true;
    error.value = null;
    try {
      const result = await request(...args);
      if (call !== lastCall) return null;
      data.value = result;
      return result;
    } catch (caught) {
      if (call === lastCall) error.value = toMessage(caught);
      return null;
    } finally {
      if (call === lastCall) isLoading.value = false;
    }
  }

  return { data, isLoading, error, run };
}
