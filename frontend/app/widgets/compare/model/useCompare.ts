// Сравнение периодов: два периода, готовые варианты, ответ сервера.
// Выбрали период в календаре - сравнение пересчитывается само
import type { Ref } from 'vue';
import { onMounted } from 'vue';
import { useSession, useSessionState } from '~/entities/session';
import { type Comparison, toApiError } from '~/shared/api';
import { useRequest } from '~/shared/lib';
import type { DateRange } from '~/shared/ui';
import { fetchComparison } from '../api/compare-api';
import { type PeriodPair, type Preset, PRESETS, presetPeriods } from '../lib/presets';

export interface UseCompare {
  pair: Ref<PeriodPair>;
  /** Выбранный готовый вариант; null - периоды выбраны в календаре. */
  preset: Ref<Preset | null>;
  data: Ref<Comparison | null>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  /** Выбран период в календаре - сравнить. */
  setPeriod: (period: keyof PeriodPair, range: DateRange) => Promise<void>;
  /** Готовый вариант: поставить периоды и сравнить. */
  applyPreset: (value: Preset) => Promise<void>;
}

/**
 * Сравнение двух периодов. При открытии - последний полный месяц против предыдущего.
 * @returns {UseCompare} периоды, варианты, ответ и действия.
 */
export function useCompare(): UseCompare {
  const session = useSession();
  const dataEnd = session.state.value.prepared?.date_to;

  // Периоды, выбранный вариант и ответ переживают переключение вкладок
  const pair = useSessionState<PeriodPair>('compare-pair', () => ({
    first: { from: '', to: '' },
    second: { from: '', to: '' },
  }));
  const preset = useSessionState<Preset | null>('compare-preset', () => null);

  const { data, isLoading, error, run } = useRequest(
    fetchComparison,
    err => toApiError(err).message,
    useSessionState<Comparison | null>('compare-data', () => null),
  );

  /** Сравнить, если оба периода выбраны. */
  async function compare(): Promise<void> {
    const { first, second } = pair.value;
    if (!first.from || !first.to || !second.from || !second.to) return;
    await run({ first: { ...first }, second: { ...second } });
  }

  /**
   * Период выбран в календаре - это уже не готовый вариант.
   * @param {keyof PeriodPair} period - first (было) или second (стало).
   * @param {DateRange} range - выбранный период.
   */
  async function setPeriod(period: keyof PeriodPair, range: DateRange): Promise<void> {
    pair.value[period] = { ...range };
    preset.value = null;
    await compare();
  }

  /**
   * Готовый вариант: периоды от последнего дня данных - и сразу сравнение.
   * @param {Preset} value - какой вариант.
   */
  async function applyPreset(value: Preset): Promise<void> {
    if (!dataEnd) return;
    pair.value = presetPeriods(value, dataEnd);
    preset.value = value;
    await compare();
  }

  // Первый заход - месяц к месяцу; вернулись на вкладку - прежнее сравнение уже на экране
  onMounted(() => {
    if (!data.value) applyPreset(PRESETS.monthToMonth);
  });

  return { pair, preset, data, isLoading, error, setPeriod, applyPreset };
}
