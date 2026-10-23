import { LOCALE } from '~/shared/config';

const MONTH_INDEX_SHIFT = 1; // в строке месяц 1-12, в Date - 0-11
const ISO_PART_LENGTH = { month: 2, day: 2 } as const;

/** Как показывать месяц: полностью - в тексте, коротко - на осях графиков. */
export const MONTH_STYLES = {
  long: 'long',
  short: 'short',
} as const;

export type MonthStyle = (typeof MONTH_STYLES)[keyof typeof MONTH_STYLES];

/**
 * Строка даты с сервера → дата в местном времени.
 * Не через new Date("2026-10-01"): такую строку браузер читает как полночь по Гринвичу,
 * и западнее Гринвича она превращается в предыдущий день.
 * @param {string} value - "2026-10-01" или "2026-09" (тогда - первое число месяца).
 * @returns {Date} дата в местном времени.
 */
export function parseIsoDate(value: string): Date {
  const [year, month, day = 1] = value.split('-').map(Number);
  return new Date(year, month - MONTH_INDEX_SHIFT, day);
}

/**
 * Дата для запросов к API: местная дата → "2026-10-01".
 * @param {Date} date - дата.
 * @returns {string} дата в формате ГГГГ-ММ-ДД.
 */
export function toIsoDate(date: Date): string {
  const month = String(date.getMonth() + MONTH_INDEX_SHIFT).padStart(ISO_PART_LENGTH.month, '0');
  const day = String(date.getDate()).padStart(ISO_PART_LENGTH.day, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

/**
 * Дата для показа: "2026-10-01" → "01.10.2026".
 * @param {string} value - дата с сервера.
 * @returns {string} дата для показа.
 */
export function formatDate(value: string): string {
  return new Intl.DateTimeFormat(LOCALE, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(parseIsoDate(value));
}

/**
 * Месяц для показа: "2026-09" → "сентябрь 2026" или коротко "сент. 2026".
 * @param {string} value - месяц с сервера ("2026-09") или дата.
 * @param {MonthStyle} [style=MONTH_STYLES.long] - полностью или коротко.
 * @returns {string} месяц для показа.
 */
export function formatMonth(value: string, style: MonthStyle = MONTH_STYLES.long): string {
  const parts = new Intl.DateTimeFormat(LOCALE, { month: style, year: 'numeric' })
    .formatToParts(parseIsoDate(value))
    .filter(part => part.type === 'month' || part.type === 'year');
  // Intl добавляет "г." после года ("сентябрь 2026 г.") - берём только месяц и год
  return parts.map(part => part.value).join(' ');
}
