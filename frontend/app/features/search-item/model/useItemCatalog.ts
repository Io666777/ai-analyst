// Каталог товаров под поиском: загружается один раз, фильтруется на каждую букву в браузере.
// Не нашлось по названию - спрашиваем сервер: он ищет и по артикулу, и по другим признакам
import type { ComputedRef, Ref } from 'vue';
import { computed, onMounted, ref } from 'vue';
import { useSessionState } from '~/entities/session';
import { type Catalog, type ItemsFound, toApiError, type TopRow } from '~/shared/api';
import { useRequest } from '~/shared/lib';
import { fetchCatalog, searchItems } from '../api/search-api';
import { filterItems } from '../lib/filter-items';

/** Больше строк сразу не рисуем - список и так листают редко, а страница не тормозит. */
export const VISIBLE_LIMIT = 200;
/** Как на сервере: длиннее запрос не примет. */
export const QUERY_MAX_LENGTH = 100;

export interface UseItemCatalog {
  query: Ref<string>;
  catalog: Ref<Catalog | null>;
  /** Подходящие под запрос товары - все, а не только показанные. */
  matched: ComputedRef<TopRow[]>;
  /** Показанные строки - не больше VISIBLE_LIMIT. */
  visible: ComputedRef<TopRow[]>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  /** Ответ сервера на поиск по признакам (артикул) - когда по названию ничего. */
  serverFound: Ref<ItemsFound | null>;
  isSearching: Ref<boolean>;
  /** Искать на сервере - по артикулу и другим признакам. */
  searchServer: () => Promise<ItemsFound | null>;
}

/**
 * Каталог товаров с фильтром.
 * @returns {UseItemCatalog} запрос, каталог, подходящие строки и поиск на сервере.
 */
export function useItemCatalog(): UseItemCatalog {
  const toMessage = (err: unknown) => toApiError(err).message;
  const query = ref('');

  // Каталог - один раз за версию данных: вернулись на вкладку - список уже есть
  const { data: catalog, isLoading, error, run } = useRequest(
    fetchCatalog,
    toMessage,
    useSessionState<Catalog | null>('item-catalog', () => null),
  );
  const server = useRequest(searchItems, toMessage);

  const matched = computed(() => filterItems(catalog.value?.items ?? [], query.value));
  const visible = computed(() => matched.value.slice(0, VISIBLE_LIMIT));

  /**
   * Поиск на сервере по введённому тексту.
   * @returns {Promise<ItemsFound | null>} найденное; null - пустой запрос или ошибка.
   */
  function searchServer(): Promise<ItemsFound | null> {
    const text = query.value.trim().slice(0, QUERY_MAX_LENGTH);
    if (!text) return Promise.resolve(null);
    return server.run(text);
  }

  onMounted(() => {
    if (!catalog.value) run();
  });

  return {
    query,
    catalog,
    matched,
    visible,
    isLoading,
    error,
    serverFound: server.data,
    isSearching: server.isLoading,
    searchServer,
  };
}
