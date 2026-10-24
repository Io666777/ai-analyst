import { LOCALE } from '~/shared/config';
import { formatNumber } from './format-number';

/** Три формы слова: 1 строка, 2 строки, 5 строк. */
export interface WordForms {
  one: string;
  few: string;
  many: string;
}

// Встроенные русские правила: 1, 21, 101 - one; 2-4, 22-24 - few; 0, 5-20, 11-14 - many
const pluralRules = new Intl.PluralRules(LOCALE);

/**
 * Число со словом в правильной форме: 1 строка, 2 строки, 5 строк, 2 921 строка.
 * Для счётчиков - строк, колонок, дней: число показывается целым.
 * @param {number} count - целое число.
 * @param {WordForms} forms - три формы слова.
 * @returns {string} "2 921 строка".
 */
export function pluralize(count: number, forms: WordForms): string {
  const category = pluralRules.select(count);
  const FORM_BY_CATEGORY: Record<string, string> = {
    one: forms.one,
    few: forms.few,
    many: forms.many,
  };
  return `${formatNumber(count)} ${FORM_BY_CATEGORY[category] ?? forms.many}`;
}
