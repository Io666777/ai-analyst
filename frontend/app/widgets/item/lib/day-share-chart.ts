// Рецепт кольца «место товара в продажах дня»: вся выручка дня, наш товар - основным цветом,
// другие товары дня - приглушёнными оттенками, всё прочее - серым «Остальное»
import type { DeepReadonly } from 'vue';
import type { TopRow } from '~/shared/api';
import { formatMoney, formatPercent } from '~/shared/lib';
import type { ChartOption, ChartPalette } from '~/shared/ui';

const REST_NAME = 'Остальное';
const OTHERS_SHOWN = 5; // других товаров дня своими секторами - остальное в серый
const RING_RADIUS = ['42%', '68%'];
const RING_CENTER = ['50%', '44%'];
const GAP_WIDTH = 2;
const OTHER_OPACITY = 0.45; // другие товары - бледнее: глаз сразу находит наш
const MIN_LABEL_PERCENT = 4;
const LABEL_FONT_SIZE = 11;

interface Slice {
  name: string;
  value: number;
  share: number;
  isItem: boolean;
}

/**
 * Секторы дня: наш товар (или товары - для «всех вместе»), другие товары дня, остальное.
 * @param {object} data - данные дня.
 * @param {string[]} data.items - наши товары.
 * @param {number} data.itemValue - выручка наших товаров за день.
 * @param {DeepReadonly<TopRow[]>} data.top - лучшие товары дня.
 * @param {number} data.total - вся выручка дня.
 * @returns {Slice[]} секторы кольца.
 */
export function daySlices(data: {
  items: readonly string[];
  itemValue: number;
  top: DeepReadonly<TopRow[]>;
  total: number;
}): Slice[] {
  const { items, itemValue, top, total } = data;
  if (!total) return [];
  const share = (value: number) => (value / total) * 100;
  const label = items.length === 1 ? items[0] : `Выбранные (${items.length})`;

  const slices: Slice[] = [{ name: label, value: itemValue, share: share(itemValue), isItem: true }];
  top
    .filter(row => !items.includes(row.name))
    .slice(0, OTHERS_SHOWN)
    .forEach(row => {
      slices.push({ name: row.name, value: row.value, share: share(row.value), isItem: false });
    });

  const rest = total - slices.reduce((sum, slice) => sum + slice.value, 0);
  if (rest / total >= 0.001) {
    slices.push({ name: REST_NAME, value: rest, share: share(rest), isItem: false });
  }
  return slices;
}

/**
 * Настройки ECharts для кольца дня.
 * @param {Slice[]} slices - секторы (daySlices).
 * @param {string} currency - валюта.
 * @param {ChartPalette} palette - цвета (readChartPalette).
 * @returns {ChartOption} настройки для VChart.
 */
export function dayShareOption(
  slices: Slice[],
  currency: string,
  palette: ChartPalette,
): ChartOption {
  return {
    tooltip: {
      trigger: 'item',
      formatter: ({ data: slice }: { data: Slice }) =>
        `${slice.name}<br>${formatMoney(slice.value, currency)} · ${formatPercent(slice.share, false)}`,
    },
    legend: { type: 'scroll', top: 'auto', bottom: 0, left: 'center' },
    // Общий вид графиков (VChart) задаёт оси - у кольца их нет, прячем
    xAxis: { show: false },
    yAxis: { show: false },
    series: [
      {
        name: 'Доля в выручке дня',
        type: 'pie',
        radius: RING_RADIUS,
        center: RING_CENTER,
        itemStyle: { borderColor: palette.gap, borderWidth: GAP_WIDTH },
        label: {
          position: 'inside',
          fontSize: LABEL_FONT_SIZE,
          fontWeight: 600,
          color: palette.text,
          formatter: ({ data: slice }: { data: Slice }) =>
            slice.share >= MIN_LABEL_PERCENT ? formatPercent(slice.share, false) : '',
        },
        labelLine: { show: false },
        data: slices.map((slice, index) => {
          if (slice.isItem) {
            return {
              ...slice,
              itemStyle: { color: palette.categories[0] },
              label: { color: palette.gap },
            };
          }
          const color =
            slice.name === REST_NAME
              ? palette.rest
              : palette.categories[index % palette.categories.length];
          return { ...slice, itemStyle: { color, opacity: slice.name === REST_NAME ? 1 : OTHER_OPACITY } };
        }),
      },
    ],
  };
}
