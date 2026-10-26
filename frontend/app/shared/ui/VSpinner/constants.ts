/** Размер индикатора загрузки: small - внутри кнопки, medium - в блоке, large - на весь экран. */
export const SPINNER_SIZES = {
  small: 'small',
  medium: 'medium',
  large: 'large',
} as const;

export type SpinnerSize = (typeof SPINNER_SIZES)[keyof typeof SPINNER_SIZES];
