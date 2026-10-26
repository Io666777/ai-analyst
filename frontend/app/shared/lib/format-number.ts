import { DEFAULT_CURRENCY, EMPTY_VALUE, LOCALE } from '~/shared/config';

const PERCENT_FRACTION_DIGITS = 1; // проценты - с одним знаком: −7,6%
const PERCENT_DIVIDER = 100; // сервер присылает -7.6, а Intl ждёт долю: -0.076

/**
 * Число с пробелами между тысячами: 18740.5 → "18 741".
 * @param {number} value - число.
 * @param {number} [fractionDigits=0] - сколько знаков после запятой.
 * @returns {string} число для показа.
 */
export function formatNumber(value: number, fractionDigits = 0): string {
  return new Intl.NumberFormat(LOCALE, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

/**
 * Деньги: 18740.5 → "18 741 р.". Валюта - строкой с сервера ("р.", "$", "£"),
 * поэтому не через currency-формат Intl: он знает только коды вроде BYN и USD.
 * @param {number} value - сумма.
 * @param {string} [currency=DEFAULT_CURRENCY] - валюта из настроек сессии.
 * @returns {string} сумма для показа.
 */
export function formatMoney(value: number, currency: string = DEFAULT_CURRENCY): string {
  return `${formatNumber(value)} ${currency}`;
}

/**
 * Процент изменения: -7.6 → "−7,6%", 7.2 → "+7,2%", null → "—".
 * null приходит с сервера, когда процент посчитать нельзя (было 0).
 * @param {number | null} value - процент, как его прислал сервер (-7.6, а не -0.076).
 * @param {boolean} [signed=true] - показывать плюс у роста.
 * @returns {string} процент для показа.
 */
export function formatPercent(value: number | null, signed = true): string {
  if (value === null) return EMPTY_VALUE;
  return new Intl.NumberFormat(LOCALE, {
    style: 'percent',
    maximumFractionDigits: PERCENT_FRACTION_DIGITS,
    signDisplay: signed ? 'exceptZero' : 'auto',
  }).format(value / PERCENT_DIVIDER);
}
