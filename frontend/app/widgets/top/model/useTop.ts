// Топ: выбранные параметры и ответ сервера. Поменяли параметр - топ пересчитался сам.
// Параметры и ответ переживают переключение вкладок (useSessionState)
import type { ComputedRef, Ref, WritableComputedRef } from 'vue';
import { computed, onMounted, toRef, watch } from 'vue';
import { useSession, useSessionState } from '~/entities/session';
import { type Top, toApiError } from '~/shared/api';
import { TOP_LIMITS } from '~/shared/config';
import { useRequest } from '~/shared/lib';
import type { DateRange, SelectOption } from '~/shared/ui';
import { fetchTop } from '~/entities/sale';
import { TOP_PERIODS, type TopPeriod, topPeriodDates } from '../lib/periods';

/** Сколько строк можно выбрать - не больше, чем разрешает сервер. */
const TOP_SIZES = [5, TOP_LIMITS.default, 20, TOP_LIMITS.max] as const;

/** С чего начать: товар, если его разметили, иначе категория. */
const PREFERRED_FIELDS = ['object', 'category'] as const;

interface TopParams {
  by: string | undefined;
  /** Сколько строк - строкой, как в списке выбора. */
  size: string;
  worst: boolean;
  /** Период: пусто - без ограничения с этой стороны. */
  dateFrom: string;
  dateTo: string;
  /** Выбранный быстрый период; null - даты введены руками. */
  period: TopPeriod | null;
}

export interface UseTop {
  /** Поле топа для списка выбора. */
  field: WritableComputedRef<string>;
  size: Ref<string>;
  worst: Ref<boolean>;
  dateFrom: Ref<string>;
  dateTo: Ref<string>;
  period: Ref<TopPeriod | null>;
  data: Ref<Top | null>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  fieldOptions: ComputedRef<SelectOption[]>;
  sizeOptions: SelectOption[];
  /** Выбрать период в календаре - это уже не быстрый период; пустой - за всё время. */
  setRange: (range: DateRange) => void;
  /** Быстрый период: поставить даты. */
  applyPeriod: (value: TopPeriod) => void;
  reload: () => Promise<Top | null>;
}

/**
 * Топ с параметрами.
 * @returns {UseTop} параметры, ответ и состояние загрузки.
 */
export function useTop(): UseTop {
  const session = useSession();
  const prepared = session.state.value.prepared;
  const fields = prepared?.fields ?? [];

  const params = useSessionState<TopParams>('top-params', () => ({
    by: PREFERRED_FIELDS.find(field => fields.includes(field)),
    size: String(TOP_LIMITS.default),
    worst: false,
    dateFrom: '',
    dateTo: '',
    period: TOP_PERIODS.all,
  }));
  const by = toRef(params.value, 'by');
  const size = toRef(params.value, 'size');
  const worst = toRef(params.value, 'worst');
  const dateFrom = toRef(params.value, 'dateFrom');
  const dateTo = toRef(params.value, 'dateTo');
  const period = toRef(params.value, 'period');

  const { data, isLoading, error, run } = useRequest(
    fetchTop,
    err => toApiError(err).message,
    useSessionState<Top | null>('top-data', () => null),
  );

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
   * Период из календаря. Сбросили - это «за всё время», подсвечиваем ту кнопку.
   * @param {DateRange} range - период; пустой - без ограничения.
   */
  function setRange(range: DateRange): void {
    dateFrom.value = range.from;
    dateTo.value = range.to;
    period.value = range.from || range.to ? null : TOP_PERIODS.all;
  }

  /**
   * Быстрый период: последние полные месяцы данных.
   * @param {TopPeriod} value - какой период.
   */
  function applyPeriod(value: TopPeriod): void {
    if (!prepared) return;
    const dates = topPeriodDates(value, prepared.date_to);
    dateFrom.value = dates.from;
    dateTo.value = dates.to;
    period.value = value;
  }

  /**
   * Запросить топ с текущими параметрами.
   * @returns {Promise<Top | null>} ответ; null - ошибка.
   */
  function reload(): Promise<Top | null> {
    return run({
      by: by.value,
      top: Number(size.value),
      worst: worst.value,
      dateFrom: dateFrom.value,
      dateTo: dateTo.value,
    });
  }

  // Вернулись на вкладку - топ уже есть, запрашивать заново незачем
  onMounted(() => {
    if (!data.value) reload();
  });
  watch([by, size, worst, dateFrom, dateTo], reload);

  return {
    field,
    size,
    worst,
    dateFrom,
    dateTo,
    period,
    data,
    isLoading,
    error,
    fieldOptions,
    sizeOptions,
    setRange,
    applyPeriod,
    reload,
  };
}
