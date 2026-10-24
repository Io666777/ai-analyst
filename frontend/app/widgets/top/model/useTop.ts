// Топ: выбранные параметры и ответ сервера. Поменяли параметр - топ пересчитался сам
import type { ComputedRef, Ref, ShallowRef, WritableComputedRef } from 'vue';
import { computed, onMounted, ref, watch } from 'vue';
import { useSession } from '~/entities/session';
import { type Top, toApiError } from '~/shared/api';
import { TOP_LIMITS } from '~/shared/config';
import { useRequest } from '~/shared/lib';
import type { SelectOption } from '~/shared/ui';
import { fetchTop } from '../api/top-api';

/** Сколько строк можно выбрать - не больше, чем разрешает сервер. */
const TOP_SIZES = [5, TOP_LIMITS.default, 20, TOP_LIMITS.max] as const;

/** С чего начать: товар, если его разметили, иначе категория. */
const PREFERRED_FIELDS = ['object', 'category'] as const;

export interface UseTop {
  /** Поле топа для списка выбора. */
  field: WritableComputedRef<string>;
  /** Сколько строк - строкой, как в списке выбора. */
  size: Ref<string>;
  worst: Ref<boolean>;
  data: ShallowRef<Top | null>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  fieldOptions: ComputedRef<SelectOption[]>;
  sizeOptions: SelectOption[];
  reload: () => Promise<Top | null>;
}

/**
 * Топ с параметрами.
 * @returns {UseTop} параметры, ответ и состояние загрузки.
 */
export function useTop(): UseTop {
  const session = useSession();
  const fields = session.state.value.prepared?.fields ?? [];

  const by = ref<string | undefined>(PREFERRED_FIELDS.find(field => fields.includes(field)));
  const size = ref(String(TOP_LIMITS.default));
  const worst = ref(false);

  const { data, isLoading, error, run } = useRequest(fetchTop, err => toApiError(err).message);

  // Поле для списка выбора: не выбрали сами - то, по которому сервер построил топ
  const field = computed({
    get: () => by.value ?? data.value?.by ?? '',
    set: (value: string) => {
      by.value = value;
    },
  });

  // Список полей приходит с первым ответом сервера
  const fieldOptions = computed<SelectOption[]>(() =>
    (data.value?.available ?? []).map(choice => ({ value: choice.value, label: choice.label })),
  );
  const sizeOptions: SelectOption[] = TOP_SIZES.map(value => ({
    value: String(value),
    label: String(value),
  }));

  /**
   * Запросить топ с текущими параметрами.
   * @returns {Promise<Top | null>} ответ; null - ошибка.
   */
  function reload(): Promise<Top | null> {
    return run({ by: by.value, top: Number(size.value), worst: worst.value });
  }

  onMounted(reload);
  watch([by, size, worst], reload);

  return { field, size, worst, data, isLoading, error, fieldOptions, sizeOptions, reload };
}
