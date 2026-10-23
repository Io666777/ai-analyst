/** Направление изменения: рост, падение, без изменений - для цвета и стрелки у цифры. */
export const TRENDS = {
  up: 'up',
  down: 'down',
  flat: 'flat',
} as const;

export type Trend = (typeof TRENDS)[keyof typeof TRENDS];

/**
 * Направление изменения по проценту: -7.6 → "down", 7.2 → "up", 0 или null → "flat".
 * @param {number | null} percent - изменение в процентах с сервера.
 * @returns {Trend} направление.
 */
export function trendOf(percent: number | null): Trend {
  if (percent === null || percent === 0) return TRENDS.flat;
  return percent > 0 ? TRENDS.up : TRENDS.down;
}
