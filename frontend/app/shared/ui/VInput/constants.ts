/** Тип поля ввода: текст, поиск (с крестиком очистки в браузере), число, дата (календарь). */
export const INPUT_TYPES = {
  text: 'text',
  search: 'search',
  number: 'number',
  date: 'date',
} as const;

export type InputType = (typeof INPUT_TYPES)[keyof typeof INPUT_TYPES];
