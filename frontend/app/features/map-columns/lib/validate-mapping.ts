// Проверка разметки до отправки - те же правила, что на сервере (backend/app/data/model.py),
// но ошибка видна сразу и у нужной колонки
import { COLUMN_ROLES, UNIQUE_ROLES } from '~/entities/column-role';

export const MAPPING_ERRORS = {
  noDate: 'Укажите колонку с датой - без неё продажи не привязать ко времени',
  noAmount: 'Укажите сумму - или цену и количество, тогда сумма посчитается сама',
} as const;

export interface MappingErrors {
  /** Ошибка у конкретной колонки: колонка → текст. */
  byColumn: Record<string, string>;
  /** Ошибки разметки целиком. */
  general: string[];
}

/**
 * Текст ошибки «роль уже занята».
 * @param {string} column - колонка, у которой роль уже стоит.
 * @returns {string} текст ошибки.
 */
function duplicateError(column: string): string {
  return `Эта роль уже у колонки «${column}»`;
}

/**
 * Проверяет разметку: дата есть, основная роль - только у одной колонки, есть чем считать деньги.
 * @param {Record<string, string>} mapping - колонка → роль.
 * @returns {MappingErrors} ошибки; пустые - разметка подходит.
 */
export function validateMapping(mapping: Readonly<Record<string, string>>): MappingErrors {
  const byColumn: Record<string, string> = {};
  const firstColumnWithRole: Record<string, string> = {};

  Object.entries(mapping).forEach(([column, role]) => {
    if (!UNIQUE_ROLES.includes(role)) return;
    const owner = firstColumnWithRole[role];
    if (owner) byColumn[column] = duplicateError(owner);
    else firstColumnWithRole[role] = column;
  });

  const roles = new Set(Object.values(mapping));
  const hasMoney =
    roles.has(COLUMN_ROLES.amount) ||
    (roles.has(COLUMN_ROLES.price) && roles.has(COLUMN_ROLES.quantity));

  const general = [
    ...(roles.has(COLUMN_ROLES.date) ? [] : [MAPPING_ERRORS.noDate]),
    ...(hasMoney ? [] : [MAPPING_ERRORS.noAmount]),
  ];
  return { byColumn, general };
}

/**
 * Есть ли в проверке хоть одна ошибка.
 * @param {MappingErrors} errors - результат validateMapping.
 * @returns {boolean} true - разметку отправлять нельзя.
 */
export function hasMappingErrors(errors: MappingErrors): boolean {
  return errors.general.length > 0 || Object.keys(errors.byColumn).length > 0;
}
