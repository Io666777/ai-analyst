// Роли колонок - как их понимает сервер (backend/app/data/model.py).
// Подписи для показа приходят с сервера (/api/options), здесь - только значения и правила

/** Роль колонки файла. */
export const COLUMN_ROLES = {
  date: 'date',
  object: 'object',
  category: 'category',
  quantity: 'quantity',
  amount: 'amount',
  price: 'price',
  receipt: 'receipt',
  executor: 'executor',
  attribute: 'attribute',
  measure: 'measure',
  person: 'person',
  ignore: 'ignore',
} as const;

export type ColumnRole = (typeof COLUMN_ROLES)[keyof typeof COLUMN_ROLES];

/**
 * Основные поля - у каждого особый смысл, поэтому такая роль может быть только у одной колонки.
 * Остальные (признак, показатель, клиент, «не нужна») - у скольких угодно.
 */
export const UNIQUE_ROLES: readonly string[] = [
  COLUMN_ROLES.date,
  COLUMN_ROLES.object,
  COLUMN_ROLES.category,
  COLUMN_ROLES.quantity,
  COLUMN_ROLES.amount,
  COLUMN_ROLES.price,
  COLUMN_ROLES.receipt,
  COLUMN_ROLES.executor,
];
