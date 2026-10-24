// Готовые пары периодов: считаются от последней даты в данных, а не от сегодня -
// выгрузка может быть старой, и «прошлый месяц» от сегодня оказался бы пустым
import { daysBefore, lastFullMonth, type Period, wholeMonth } from '~/shared/lib';

export type { Period } from '~/shared/lib';

export interface PeriodPair {
  /** Было. */
  first: Period;
  /** Стало. */
  second: Period;
}

export const PRESETS = {
  monthToMonth: 'monthToMonth',
  yearToYear: 'yearToYear',
  last30Days: 'last30Days',
} as const;

export type Preset = (typeof PRESETS)[keyof typeof PRESETS];

export const PRESET_LABELS: Record<Preset, string> = {
  [PRESETS.monthToMonth]: 'Месяц к месяцу',
  [PRESETS.yearToYear]: 'Год к году',
  [PRESETS.last30Days]: '30 дней к 30 дням',
};

const DAYS_IN_WINDOW = 30;

/**
 * Пара периодов для готового варианта.
 * @param {Preset} preset - какой вариант.
 * @param {string} dataEnd - последняя дата в данных: "2026-09-30".
 * @returns {PeriodPair} было и стало.
 */
export function presetPeriods(preset: Preset, dataEnd: string): PeriodPair {
  const { year, month } = lastFullMonth(dataEnd);

  if (preset === PRESETS.yearToYear) {
    return { first: wholeMonth(year - 1, month), second: wholeMonth(year, month) };
  }
  if (preset === PRESETS.last30Days) {
    return {
      first: {
        from: daysBefore(dataEnd, 2 * DAYS_IN_WINDOW - 1),
        to: daysBefore(dataEnd, DAYS_IN_WINDOW),
      },
      second: { from: daysBefore(dataEnd, DAYS_IN_WINDOW - 1), to: dataEnd },
    };
  }
  return { first: wholeMonth(year, month - 1), second: wholeMonth(year, month) };
}
