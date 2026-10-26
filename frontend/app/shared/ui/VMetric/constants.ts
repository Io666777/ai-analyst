/** Как показать значение: деньги ("18 740 р."), число ("39 716") или процент ("27,5 %"). */
export const METRIC_FORMATS = {
  money: 'money',
  number: 'number',
  percent: 'percent',
} as const;

export type MetricFormat = (typeof METRIC_FORMATS)[keyof typeof METRIC_FORMATS];
