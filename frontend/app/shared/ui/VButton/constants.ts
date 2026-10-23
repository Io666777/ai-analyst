/** Внешний вид кнопки: заливка - главное действие, обводка - второстепенное, текст - третьестепенное. */
export const BUTTON_VARIANTS = {
  primary: 'primary',
  secondary: 'secondary',
  ghost: 'ghost',
} as const;

/** Размер кнопки. */
export const BUTTON_SIZES = {
  medium: 'medium',
  small: 'small',
} as const;

export type ButtonVariant = (typeof BUTTON_VARIANTS)[keyof typeof BUTTON_VARIANTS];
export type ButtonSize = (typeof BUTTON_SIZES)[keyof typeof BUTTON_SIZES];
