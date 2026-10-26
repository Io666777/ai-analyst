// Состояние раздела, которое переживает переключение вкладок: найденный товар, параметры топа,
// даты сравнения, посчитанный прогноз. Сбрасывается само, когда данные поменялись
// (новый файл, разметка, настройки) - иначе на экране остались бы цифры по старым данным
import type { Ref } from 'vue';
import { computed } from 'vue';
import { useState } from '#imports';
import { useSession } from './useSession';

interface Stored<T> {
  version: number;
  value: T;
}

/**
 * Запомнить состояние раздела на время работы с текущими данными.
 * @param {string} key - уникальное имя: "top-params", "compare-periods"...
 * @param {() => T} init - начальное значение (и значение после сброса).
 * @returns {Ref<T>} состояние: читать и менять как обычный ref.
 */
export function useSessionState<T>(key: string, init: () => T): Ref<T> {
  const session = useSession();
  const stored = useState<Stored<T>>(`section:${key}`, () => ({
    version: session.state.value.dataVersion,
    value: init(),
  }));

  // Данные поменялись с прошлого раза - начинаем заново
  if (stored.value.version !== session.state.value.dataVersion) {
    stored.value = { version: session.state.value.dataVersion, value: init() };
  }

  return computed({
    get: () => stored.value.value,
    set: value => {
      stored.value = { version: session.state.value.dataVersion, value };
    },
  });
}
