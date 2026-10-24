// Готовые пары периодов: считаются от последней даты в данных, а не от сегодня -
// выгрузка может быть старой, и «прошлый месяц» от сегодня оказался бы пустым
import { parseIsoDate, toIsoDate } from '~/shared/lib';

export interface Period {
  /** С какого дня: "2026-09-01". */
  from: string;
  /** По какой день, включительно. */
  to: string;
}

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
 * Весь месяц: с первого по последнее число.
 * @param {number} year - год.
 * @param {number} month - месяц 0-11; можно выйти за границы - Date перенесёт год сам.
 * @returns {Period} период месяца.
 */
function wholeMonth(year: number, month: number): Period {
  return {
    from: toIsoDate(new Date(year, month, 1)),
    to: toIsoDate(new Date(year, month + 1, 0)), // нулевое число следующего = последнее этого
  };
}

/**
 * Последний полный месяц данных: данные кончаются 30 сентября - сентябрь,
 * 15 октября - тоже сентябрь (октябрь неполный, сравнивать его нечестно).
 * @param {Date} end - последняя дата в данных.
 * @returns {{ year: number, month: number }} год и месяц 0-11.
 */
function lastFullMonth(end: Date): { year: number; month: number } {
  const isLastDay = new Date(end.getFullYear(), end.getMonth(), end.getDate() + 1).getDate() === 1;
  return isLastDay
    ? { year: end.getFullYear(), month: end.getMonth() }
    : { year: end.getFullYear(), month: end.getMonth() - 1 };
}

/**
 * Пара периодов для готового варианта.
 * @param {Preset} preset - какой вариант.
 * @param {string} dataEnd - последняя дата в данных: "2026-09-30".
 * @returns {PeriodPair} было и стало.
 */
export function presetPeriods(preset: Preset, dataEnd: string): PeriodPair {
  const end = parseIsoDate(dataEnd);
  const { year, month } = lastFullMonth(end);

  if (preset === PRESETS.yearToYear) {
    return { first: wholeMonth(year - 1, month), second: wholeMonth(year, month) };
  }
  if (preset === PRESETS.last30Days) {
    const day = (offset: number) =>
      toIsoDate(new Date(end.getFullYear(), end.getMonth(), end.getDate() - offset));
    return {
      first: { from: day(2 * DAYS_IN_WINDOW - 1), to: day(DAYS_IN_WINDOW) },
      second: { from: day(DAYS_IN_WINDOW - 1), to: dataEnd },
    };
  }
  return { first: wholeMonth(year, month - 1), second: wholeMonth(year, month) };
}
