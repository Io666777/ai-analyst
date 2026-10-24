// Сравнение периодов: даты, готовые варианты, проверка, ответ сервера
import type { ComputedRef, Ref, ShallowRef } from 'vue';
import { computed, onMounted, ref } from 'vue';
import { useSession } from '~/entities/session';
import { type Comparison, toApiError } from '~/shared/api';
import { useRequest } from '~/shared/lib';
import { fetchComparison } from '../api/compare-api';
import { type Period, type PeriodPair, type Preset, PRESETS, presetPeriods } from '../lib/presets';
import { type PeriodErrors, validatePeriods } from '../lib/validate-periods';

/**
 * Копия пары периодов. Не structuredClone: он не копирует реактивные объекты Vue (Proxy).
 * @param {PeriodPair} pair - пара.
 * @returns {PeriodPair} независимая копия.
 */
function copyPair(pair: PeriodPair): PeriodPair {
  return { first: { ...pair.first }, second: { ...pair.second } };
}

export interface UseCompare {
  pair: Ref<PeriodPair>;
  /** Выбранный готовый вариант; null - даты введены руками. */
  preset: Ref<Preset | null>;
  /** Ошибки полей - после первой попытки сравнить. */
  errors: ComputedRef<PeriodErrors>;
  data: ShallowRef<Comparison | null>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  /** Поменять одну дату руками. */
  setDate: (period: keyof PeriodPair, edge: keyof Period, value: string) => void;
  /** Готовый вариант: поставить даты и сразу сравнить. */
  applyPreset: (value: Preset) => Promise<void>;
  /** Сравнить введённые даты. */
  submit: () => Promise<void>;
}

/**
 * Сравнение двух периодов. При открытии - последний полный месяц против предыдущего.
 * @returns {UseCompare} даты, варианты, ответ и действия.
 */
export function useCompare(): UseCompare {
  const session = useSession();
  const dataEnd = session.state.value.prepared?.date_to;

  const pair = ref<PeriodPair>({ first: { from: '', to: '' }, second: { from: '', to: '' } });
  const preset = ref<Preset | null>(null);
  const isSubmitted = ref(false);

  const { data, isLoading, error, run } = useRequest(fetchComparison, err =>
    toApiError(err).message,
  );

  const errors = computed(() => (isSubmitted.value ? validatePeriods(pair.value) : {}));

  /**
   * Поменять одну дату руками - это уже не готовый вариант.
   * @param {keyof PeriodPair} period - first (было) или second (стало).
   * @param {keyof Period} edge - from или to.
   * @param {string} value - дата "2026-09-01" или пусто.
   */
  function setDate(period: keyof PeriodPair, edge: keyof Period, value: string): void {
    pair.value[period][edge] = value;
    preset.value = null;
  }

  /** Проверить и сравнить. */
  async function submit(): Promise<void> {
    isSubmitted.value = true;
    if (Object.keys(validatePeriods(pair.value)).length) return;
    await run(copyPair(pair.value));
  }

  /**
   * Готовый вариант: даты от последнего дня данных - и сразу сравнение.
   * @param {Preset} value - какой вариант.
   */
  async function applyPreset(value: Preset): Promise<void> {
    if (!dataEnd) return;
    pair.value = presetPeriods(value, dataEnd);
    preset.value = value;
    await submit();
  }

  onMounted(() => applyPreset(PRESETS.monthToMonth));

  return { pair, preset, errors, data, isLoading, error, setDate, applyPreset, submit };
}
