// Рецепт графика «товары: было и стало»: пары горизонтальных столбцов,
// самый заметный товар - сверху. Подсказка - было, стало и разница
import type { DeepReadonly } from 'vue';
import type { CompareRow } from '~/shared/api';
import { formatMoney, formatPercent } from '~/shared/lib';
import type { ChartOption, ChartPalette } from '~/shared/ui';

const SERIES = { first: 'было', second: 'стало' } as const;
const NAME_WIDTH = 110; // длинные названия обрезаются, целиком - в подсказке
const BAR_MAX_WIDTH = 14;

/**
 * Настройки ECharts для пар столбцов «было / стало».
 * @param {DeepReadonly<CompareRow[]>} rows - товары в порядке сервера.
 * @param {string} currency - валюта.
 * @param {ChartPalette} palette - цвета (readChartPalette).
 * @returns {ChartOption} настройки для VChart.
 */
export function compareChartOption(
  rows: DeepReadonly<CompareRow[]>,
  currency: string,
  palette: ChartPalette,
): ChartOption {
  const shown = [...rows].reverse(); // ECharts рисует снизу вверх - переворачиваем
  return {
    legend: { data: [SERIES.first, SERIES.second] },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (items: { dataIndex: number }[]) => {
        const row = shown[items[0].dataIndex];
        const sign = row.change > 0 ? '+' : '';
        return [
          row.name,
          `${SERIES.first}: ${formatMoney(row.first, currency)}`,
          `${SERIES.second}: ${formatMoney(row.second, currency)}`,
          `разница: ${sign}${formatMoney(row.change, currency)} (${formatPercent(row.change_percent)})`,
        ].join('<br>');
      },
    },
    xAxis: { type: 'value', axisLabel: { formatter: (value: number) => formatMoney(value, '') } },
    yAxis: {
      type: 'category',
      data: shown.map(row => row.name),
      axisLabel: { width: NAME_WIDTH, overflow: 'truncate' },
    },
    series: [
      {
        name: SERIES.first,
        type: 'bar',
        barMaxWidth: BAR_MAX_WIDTH,
        itemStyle: { color: palette.rest },
        data: shown.map(row => row.first),
      },
      {
        name: SERIES.second,
        type: 'bar',
        barMaxWidth: BAR_MAX_WIDTH,
        itemStyle: { color: palette.categories[0] },
        data: shown.map(row => row.second),
      },
    ],
  };
}
