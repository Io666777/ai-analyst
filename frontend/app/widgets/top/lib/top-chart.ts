// Рецепт графика топа: кольцо долей в выручке периода. Первые строки - своими секторами,
// всё прочее - серым сектором «Остальное», чтобы кольцо было честным: 100 % = вся выручка
import type { DeepReadonly } from 'vue';
import type { TopRow } from '~/shared/api';
import { formatMoney, formatPercent } from '~/shared/lib';
import type { ChartOption, ChartPalette } from '~/shared/ui';

/** Больше секторов - тонкие полоски не различить; все строки всё равно есть в таблице. */
export const CHART_MAX_ROWS = 8;

const REST_NAME = 'Остальное';
const RING_RADIUS = ['42%', '68%']; // кольцо, а не круг: так доли легче сравнивать глазом
const RING_CENTER = ['50%', '44%']; // чуть выше середины: снизу - легенда
const GAP_WIDTH = 2; // зазор между секторами - цвета фона
const MIN_LABEL_PERCENT = 4;
const LABEL_FONT_SIZE = 11; // у совсем узких секторов подписи нет - они бы наползали

interface Slice {
  name: string;
  value: number;
  share: number;
}

interface TooltipParams {
  name: string;
  value: number;
  data: Slice;
}

/**
 * Секторы: первые строки топа и «Остальное» - разница до всей выручки периода.
 * @param {DeepReadonly<TopRow[]>} rows - строки топа.
 * @param {number} total - вся выручка периода.
 * @returns {Slice[]} секторы кольца.
 */
export function topSlices(rows: DeepReadonly<TopRow[]>, total: number): Slice[] {
  const shown = rows.slice(0, CHART_MAX_ROWS).map(row => ({
    name: row.name,
    value: row.value,
    share: row.share_percent,
  }));
  const rest = total - shown.reduce((sum, slice) => sum + slice.value, 0);
  // Копейки от округления - не «остальное»
  if (total > 0 && rest / total >= 0.001) {
    shown.push({ name: REST_NAME, value: rest, share: (rest / total) * 100 });
  }
  return shown;
}

/**
 * Настройки ECharts для кольца топа.
 * @param {object} data - данные.
 * @param {DeepReadonly<TopRow[]>} data.rows - строки топа.
 * @param {number} data.total - вся выручка периода.
 * @param {string} data.currency - валюта.
 * @param {ChartPalette} palette - цвета (readChartPalette).
 * @returns {ChartOption} настройки для VChart.
 */
export function topChartOption(
  data: { rows: DeepReadonly<TopRow[]>; total: number; currency: string },
  palette: ChartPalette,
): ChartOption {
  const slices = topSlices(data.rows, data.total);
  return {
    tooltip: {
      trigger: 'item',
      formatter: ({ name, value, data: slice }: TooltipParams) =>
        `${name}<br>${formatMoney(value, data.currency)} · ${formatPercent(slice.share, false)}`,
    },
    legend: { type: 'scroll', top: 'auto', bottom: 0, left: 'center' },
    // Общий вид графиков (VChart) задаёт оси - у кольца их нет, прячем
    xAxis: { show: false },
    yAxis: { show: false },
    series: [
      {
        name: 'Доля в выручке',
        type: 'pie',
        radius: RING_RADIUS,
        center: RING_CENTER,
        avoidLabelOverlap: true,
        itemStyle: { borderColor: palette.gap, borderWidth: GAP_WIDTH },
        // Проценты - внутри секторов: снаружи на узком экране они обрезаются краем графика
        label: {
          position: 'inside',
          fontSize: LABEL_FONT_SIZE,
          fontWeight: 600,
          color: palette.gap,
          formatter: ({ data: slice }: { data: Slice }) =>
            slice.share >= MIN_LABEL_PERCENT ? formatPercent(slice.share, false) : '',
        },
        labelLine: { show: false },
        data: slices.map((slice, index) => {
          const isRest = slice.name === REST_NAME;
          return {
            ...slice,
            itemStyle: {
              color: isRest ? palette.rest : palette.categories[index % palette.categories.length],
            },
            // «Остальное» светло-серое - белый текст на нём не прочитать
            ...(isRest ? { label: { color: palette.text } } : {}),
          };
        }),
      },
    ],
  };
}
