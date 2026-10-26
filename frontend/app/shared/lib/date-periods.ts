// Периоды дат для отчётов: целый месяц, последний полный месяц, последние N дней.
// Считаются от последней даты в данных, а не от сегодня: выгрузка может быть старой
import { parseIsoDate, toIsoDate } from './format-date';

export interface Period {
  /** С какого дня: "2026-09-01". */
  from: string;
  /** По какой день, включительно. */
  to: string;
}

/**
 * Весь месяц: с первого по последнее число.
 * @param {number} year - год.
 * @param {number} month - месяц 0-11; можно выйти за границы - Date перенесёт год сам.
 * @returns {Period} период месяца.
 */
export function wholeMonth(year: number, month: number): Period {
  return {
    from: toIsoDate(new Date(year, month, 1)),
    to: toIsoDate(new Date(year, month + 1, 0)), // нулевое число следующего = последнее этого
  };
}

/**
 * Последний полный месяц данных: данные кончаются 30 сентября - сентябрь,
 * 15 октября - тоже сентябрь (октябрь неполный, сравнивать его нечестно).
 * @param {string} dataEnd - последняя дата в данных: "2026-09-30".
 * @returns {{ year: number, month: number }} год и месяц 0-11.
 */
export function lastFullMonth(dataEnd: string): { year: number; month: number } {
  const end = parseIsoDate(dataEnd);
  const isLastDay = new Date(end.getFullYear(), end.getMonth(), end.getDate() + 1).getDate() === 1;
  return { year: end.getFullYear(), month: end.getMonth() - (isLastDay ? 0 : 1) };
}

/**
 * Дата за days дней до указанной.
 * @param {string} date - дата "2026-09-30".
 * @param {number} days - на сколько дней назад.
 * @returns {string} дата "2026-09-01".
 */
export function daysBefore(date: string, days: number): string {
  const day = parseIsoDate(date);
  return toIsoDate(new Date(day.getFullYear(), day.getMonth(), day.getDate() - days));
}
