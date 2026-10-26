// Быстрые периоды топа: за всё время, последний полный месяц, 3 месяца, год
import { lastFullMonth, type Period, wholeMonth } from '~/shared/lib';

export const TOP_PERIODS = {
  all: 'all',
  month: 'month',
  quarter: 'quarter',
  year: 'year',
} as const;

export type TopPeriod = (typeof TOP_PERIODS)[keyof typeof TOP_PERIODS];

export const TOP_PERIOD_LABELS: Record<TopPeriod, string> = {
  [TOP_PERIODS.all]: 'За всё время',
  [TOP_PERIODS.month]: 'Последний месяц',
  [TOP_PERIODS.quarter]: '3 месяца',
  [TOP_PERIODS.year]: '12 месяцев',
};

/** Сколько полных месяцев в периоде (для «всего времени» - ограничения нет). */
const MONTHS: Record<Exclude<TopPeriod, 'all'>, number> = {
  [TOP_PERIODS.month]: 1,
  [TOP_PERIODS.quarter]: 3,
  [TOP_PERIODS.year]: 12,
};

/**
 * Даты быстрого периода: последние полные месяцы данных.
 * @param {TopPeriod} period - какой период.
 * @param {string} dataEnd - последняя дата в данных.
 * @returns {Period} даты; для «всего времени» - пустые (без ограничения).
 */
export function topPeriodDates(period: TopPeriod, dataEnd: string): Period {
  if (period === TOP_PERIODS.all) return { from: '', to: '' };
  const { year, month } = lastFullMonth(dataEnd);
  return {
    from: wholeMonth(year, month - MONTHS[period] + 1).from,
    to: wholeMonth(year, month).to,
  };
}
