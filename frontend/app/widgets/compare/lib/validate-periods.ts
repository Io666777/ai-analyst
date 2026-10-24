// Проверка дат до отправки: заполнены, начало не позже конца - как на сервере
import type { Period, PeriodPair } from './presets';

export const PERIOD_ERRORS = {
  empty: 'Укажите дату',
  reversed: 'Конец раньше начала',
} as const;

/** Ошибки полей: ключ - "first.from", "second.to"... */
export type PeriodErrors = Partial<Record<`${keyof PeriodPair}.${keyof Period}`, string>>;

/**
 * Проверяет оба периода.
 * @param {PeriodPair} pair - было и стало.
 * @returns {PeriodErrors} ошибки по полям; пусто - можно сравнивать.
 */
export function validatePeriods(pair: PeriodPair): PeriodErrors {
  const errors: PeriodErrors = {};
  (['first', 'second'] as const).forEach(key => {
    const { from, to } = pair[key];
    if (!from) errors[`${key}.from`] = PERIOD_ERRORS.empty;
    if (!to) errors[`${key}.to`] = PERIOD_ERRORS.empty;
    // ISO-даты ("2026-09-01") сравниваются как строки - порядок тот же, что у дат
    if (from && to && from > to) errors[`${key}.to`] = PERIOD_ERRORS.reversed;
  });
  return errors;
}
