// Рецепт графика топа: горизонтальные столбцы, первый - сверху, на столбце - доля «27,5 %»
import type { DeepReadonly } from 'vue';
import type { TopRow } from '~/shared/api';
import { formatMoney, formatPercent } from '~/shared/lib';
import type { ChartOption } from '~/shared/ui';

/** Больше столбцов - подписи слипаются; все строки всё равно есть в таблице. */
export const CHART_MAX_ROWS = 15;

// На столбце - только доля: подпись с суммой съедала полэкрана телефона.
// Сумма - в подсказке и в таблице под графиком
const LABEL_SPACE = 56; // место справа под «27,5 %»
const NAME_WIDTH = 110; // длинные названия обрезаются, целиком - в подсказке
const BAR_MAX_WIDTH = 28;
const TOOLBOX_SPACE = 32; // сверху - кнопка «скачать PNG», столбцы под ней

/**
 * Настройки ECharts для топа.
 * @param {DeepReadonly<TopRow[]>} rows - строки топа в порядке сервера.
 * @param {string} currency - как подписывать суммы.
 * @returns {ChartOption} настройки для VChart.
 */
export function topChartOption(rows: DeepReadonly<TopRow[]>, currency: string): ChartOption {
  const shown = rows.slice(0, CHART_MAX_ROWS).reverse(); // ECharts рисует снизу вверх
  return {
    legend: { show: false }, // ряд один - легенда ничего не объясняет
    grid: { right: LABEL_SPACE, top: TOOLBOX_SPACE },
    tooltip: {
      trigger: 'item',
      formatter: ({ dataIndex }: { dataIndex: number }) => {
        const row = shown[dataIndex];
        return `${row.name}<br>${formatMoney(row.value, currency)} · ${formatPercent(row.share_percent, false)}`;
      },
    },
    // Шкала не нужна: длину столбца видно, а точные цифры - в подписях и таблице
    xAxis: { type: 'value', axisLabel: { show: false }, splitLine: { show: false } },
    yAxis: {
      type: 'category',
      data: shown.map(row => row.name),
      axisLabel: { width: NAME_WIDTH, overflow: 'truncate' },
    },
    series: [
      {
        name: 'Выручка',
        type: 'bar',
        barMaxWidth: BAR_MAX_WIDTH,
        data: shown.map(row => row.value),
        label: {
          show: true,
          position: 'right',
          formatter: ({ dataIndex }: { dataIndex: number }) =>
            formatPercent(shown[dataIndex].share_percent, false),
        },
      },
    ],
  };
}
