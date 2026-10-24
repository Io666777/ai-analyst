// Поиск товара: ввод → пауза → подсказки с сервера
import type { Ref, ShallowRef } from 'vue';
import { onBeforeUnmount, ref, watch } from 'vue';
import { type ItemsFound, toApiError } from '~/shared/api';
import { useRequest } from '~/shared/lib';
import { searchItems } from '../api/search-api';

/** Ждём, пока человек допечатает, - не запрос на каждую букву. */
const SEARCH_DELAY_MS = 200;
/** Как на сервере: длиннее запрос не примет. */
export const QUERY_MAX_LENGTH = 100;

export interface UseItemSearch {
  query: Ref<string>;
  found: ShallowRef<ItemsFound | null>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  /** Искать сразу, без паузы (Enter). */
  searchNow: () => Promise<ItemsFound | null>;
  /** Спрятать подсказки (товар выбран). */
  reset: () => void;
  /** Поставить текст в поле без поиска (выбор пришёл из адреса страницы). */
  replaceQuery: (text: string) => void;
}

/**
 * Поиск с подсказками.
 * @param {string} initial - запрос, с которого начать (из адреса страницы).
 * @returns {UseItemSearch} запрос, подсказки и состояние.
 */
export function useItemSearch(initial = ''): UseItemSearch {
  const query = ref(initial);
  const { data: found, isLoading, error, run } = useRequest(searchItems, err =>
    toApiError(err).message,
  );
  let timer: ReturnType<typeof setTimeout> | undefined;

  /**
   * Запрос без лишних пробелов и не длиннее, чем принимает сервер.
   * @returns {string} запрос для сервера.
   */
  function cleanQuery(): string {
    return query.value.trim().slice(0, QUERY_MAX_LENGTH);
  }

  /**
   * Искать сразу.
   * @returns {Promise<ItemsFound | null>} подсказки; null - пустой запрос или ошибка.
   */
  function searchNow(): Promise<ItemsFound | null> {
    clearTimeout(timer);
    const text = cleanQuery();
    if (!text) {
      found.value = null;
      return Promise.resolve(null);
    }
    return run(text);
  }

  /** Убрать подсказки и отменить отложенный поиск - иначе он вернёт их после выбора. */
  function reset(): void {
    clearTimeout(timer);
    found.value = null;
  }

  // Текст поменяли не руками (открыли другой товар по ссылке) - искать не нужно
  let isReplacing = false;

  /**
   * Поставить текст в поле без поиска.
   * @param {string} text - новый текст.
   */
  function replaceQuery(text: string): void {
    if (text === query.value) return;
    isReplacing = true;
    query.value = text;
    reset();
  }

  watch(query, () => {
    if (isReplacing) {
      isReplacing = false;
      return;
    }
    clearTimeout(timer);
    timer = setTimeout(searchNow, SEARCH_DELAY_MS);
  });

  onBeforeUnmount(() => clearTimeout(timer));

  return { query, found, isLoading, error, searchNow, reset, replaceQuery };
}
