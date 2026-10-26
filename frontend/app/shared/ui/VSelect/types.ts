/** Вариант выпадающего списка: значение и как его показать. Так же отдаёт API (/api/options). */
export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}
