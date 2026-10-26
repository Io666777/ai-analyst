/** Адреса страниц сайта. Совпадают с файлами в app/pages. */
export const ROUTES = {
  home: '/',
  overview: '/analysis/overview',
  top: '/analysis/top',
  item: '/analysis/item',
  compare: '/analysis/compare',
  forecast: '/analysis/forecast',
} as const;

export type RoutePath = (typeof ROUTES)[keyof typeof ROUTES];
