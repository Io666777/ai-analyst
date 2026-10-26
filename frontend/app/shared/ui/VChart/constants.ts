/** Высота графика: small - в карточке товара, medium - обычный, large - прогноз с ползунком. */
export const CHART_SIZES = {
  small: 'small',
  medium: 'medium',
  large: 'large',
} as const;

export type ChartSize = (typeof CHART_SIZES)[keyof typeof CHART_SIZES];
