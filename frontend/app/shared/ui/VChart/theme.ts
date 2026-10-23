// Общий вид всех графиков - из CSS-токенов (_variables.scss).
// ECharts рисует на canvas и не понимает var(--...), поэтому значения читаем в момент отрисовки:
// поменяли токен - графики поменялись вместе с сайтом
import type { EChartsCoreOption } from 'echarts/core';

/** Цвета графиков: имя -> CSS-переменная. */
const CHART_TOKENS = {
  primary: '--primary-500',
  primaryLight: '--primary-100',
  accent: '--accent-500',
  accentLight: '--accent-300',
  text: '--base-900',
  textMuted: '--base-500',
  grid: '--base-100',
  axis: '--base-300',
  background: '--white',
} as const;

export type ChartColors = Record<keyof typeof CHART_TOKENS, string>;

const FONT_SIZE = { axis: 12, tooltip: 13 } as const;
const ZOOM_SLIDER_HEIGHT = 20;

/**
 * Цвета графиков из CSS-переменных страницы.
 * @returns {ChartColors} цвета - готовые строки для ECharts.
 */
export function readChartColors(): ChartColors {
  const styles = getComputedStyle(document.documentElement);
  const entries = Object.entries(CHART_TOKENS).map(([name, token]) => [
    name,
    styles.getPropertyValue(token).trim(),
  ]);
  return Object.fromEntries(entries) as ChartColors;
}

/**
 * Базовые настройки, общие для всех графиков: шрифт, цвета, подсказка, сетка, доступность.
 * @param {ChartColors} colors - цвета из readChartColors.
 * @returns {EChartsCoreOption} настройки ECharts.
 */
export function baseOption(colors: ChartColors): EChartsCoreOption {
  return {
    color: [colors.primary, colors.accent, colors.accentLight],
    textStyle: { fontFamily: 'inherit', color: colors.text },
    aria: { enabled: true }, // ECharts сам составит описание графика для диктора
    grid: { left: 8, right: 16, top: 40, bottom: 8, containLabel: true },
    legend: { top: 0, left: 0, textStyle: { color: colors.text }, itemGap: 16 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.background,
      borderColor: colors.axis,
      textStyle: { color: colors.text, fontSize: FONT_SIZE.tooltip },
    },
    xAxis: {
      axisLine: { lineStyle: { color: colors.axis } },
      axisLabel: { color: colors.textMuted, fontSize: FONT_SIZE.axis },
      splitLine: { show: false },
    },
    yAxis: {
      axisLabel: { color: colors.textMuted, fontSize: FONT_SIZE.axis },
      splitLine: { lineStyle: { color: colors.grid } },
    },
  };
}

/**
 * Приближение: колесо мыши и щипок внутри графика + ползунок периода снизу.
 * @param {ChartColors} colors - цвета.
 * @returns {EChartsCoreOption} настройки приближения и отступ под ползунок.
 */
export function zoomOption(colors: ChartColors): EChartsCoreOption {
  return {
    grid: { bottom: ZOOM_SLIDER_HEIGHT + 24 },
    dataZoom: [
      { type: 'inside', filterMode: 'none' },
      {
        type: 'slider',
        height: ZOOM_SLIDER_HEIGHT,
        bottom: 4,
        borderColor: colors.axis,
        fillerColor: colors.primaryLight,
        textStyle: { color: colors.textMuted },
      },
    ],
  };
}

/**
 * Кнопки над графиком: сбросить приближение и/или скачать PNG.
 * @param {object} options - какие кнопки нужны.
 * @param {boolean} options.zoomable - есть приближение - нужна кнопка "сбросить".
 * @param {string | null} options.fileName - имя файла для "скачать PNG"; null - без кнопки.
 * @returns {EChartsCoreOption} настройки панели кнопок.
 */
export function toolboxOption(options: {
  zoomable: boolean;
  fileName: string | null;
}): EChartsCoreOption {
  const feature: Record<string, object> = {};
  if (options.zoomable) feature.restore = { title: 'Сбросить приближение' };
  if (options.fileName) {
    feature.saveAsImage = { title: 'Скачать PNG', name: options.fileName, pixelRatio: 2 };
  }
  return { toolbox: { right: 0, top: 0, feature } };
}
