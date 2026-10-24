// Рецепт графика «выручка по месяцам»: линия с точками, подсказка «сентябрь 2026: 18 740 р.».
// Выбранный месяц отмечен вертикальной чертой
import type { EChartsCoreOption } from 'echarts/core';
import type { SeriesPoint } from '~/shared/api';
import { formatMoney, formatMonth, MONTH_STYLES } from '~/shared/lib';

const SERIES_NAME = 'Выручка';
const HIGHLIGHT_WIDTH = 2;

interface TooltipItem {
  axisValue: string;
  marker: string;
  seriesName: string;
  value: number;
}

/**
 * Настройки ECharts для выручки по месяцам.
 * @param {readonly SeriesPoint[]} points - месяцы ("2026-09") и выручка.
 * @param {string} currency - как подписывать суммы.
 * @param {object} [highlight] - подсветка выбранного месяца.
 * @param {string} highlight.period - месяц "2026-09".
 * @param {string} highlight.color - цвет черты.
 * @returns {EChartsCoreOption} настройки для VChart.
 */
export function revenueChartOption(
  points: readonly SeriesPoint[],
  currency: string,
  highlight?: { period: string; color: string },
): EChartsCoreOption {
  return {
    tooltip: {
      // Заголовок - месяц словами («апрель 2026»), а не как пришёл с сервера («2026-04»)
      formatter: (items: TooltipItem[]) =>
        [
          formatMonth(items[0].axisValue),
          ...items.map(
            item => `${item.marker}${item.seriesName}: ${formatMoney(item.value, currency)}`,
          ),
        ].join('<br>'),
    },
    xAxis: {
      type: 'category',
      data: points.map(point => point.period),
      axisLabel: { formatter: (period: string) => formatMonth(period, MONTH_STYLES.short) },
    },
    yAxis: { type: 'value', axisLabel: { formatter: (value: number) => formatMoney(value, '') } },
    series: [
      {
        name: SERIES_NAME,
        type: 'line',
        data: points.map(point => point.value),
        smooth: true,
        // Черта через выбранный месяц: полоса шириной в месяц у линии получилась бы нулевой
        markLine: highlight
          ? {
              silent: true,
              symbol: 'none',
              label: { show: false },
              lineStyle: { color: highlight.color, type: 'solid', width: HIGHLIGHT_WIDTH },
              data: [{ xAxis: highlight.period }],
            }
          : undefined,
      },
    ],
  };
}
