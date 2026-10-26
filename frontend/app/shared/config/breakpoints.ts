/**
 * Брейкпоинты в px: до какой ширины экрана включительно.
 * Те же числа - в assets/styles/_breakpoints.scss (там в rem). Меняются только вместе.
 */
export const BREAKPOINTS = {
  mobile: 767,
  tablet: 1279,
  laptop: 1439,
} as const;

/** Устройства по ширине экрана. desktop - всё, что шире laptop. */
export const DEVICES = {
  mobile: 'mobile',
  tablet: 'tablet',
  laptop: 'laptop',
  desktop: 'desktop',
} as const;

export type Device = (typeof DEVICES)[keyof typeof DEVICES];
