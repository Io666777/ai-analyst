// Справочник с сервера: роли колонок с подписями и страны праздников.
// Загружается один раз и запоминается - нужен и разметке, и настройкам
import type { Ref } from 'vue';
import { useState } from '#imports';
import type { Options } from '~/shared/api';
import { fetchOptions } from '../api/session-api';

const OPTIONS_STATE_KEY = 'session-options';

export interface UseOptions {
  /** Справочник; null - ещё не загружен. */
  options: Readonly<Ref<Options | null>>;
  /** Загрузить, если ещё не загружен. Ошибка - ApiError. */
  loadOptions: () => Promise<Options>;
}

/**
 * Справочник ролей и стран.
 * @returns {UseOptions} справочник и загрузка.
 */
export function useOptions(): UseOptions {
  const options = useState<Options | null>(OPTIONS_STATE_KEY, () => null);

  /**
   * Загружает справочник один раз за всё время работы вкладки.
   * @returns {Promise<Options>} справочник.
   */
  async function loadOptions(): Promise<Options> {
    if (options.value) return options.value;
    options.value = await fetchOptions();
    return options.value;
  }

  return { options, loadOptions };
}
