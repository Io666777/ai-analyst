import type { Meta, StoryObj } from '@storybook/vue3-vite';
import type { EChartsCoreOption } from 'echarts/core';
import { formatDate, formatMoney, formatMonth, formatPercent, MONTH_STYLES } from '~/shared/lib';
import { CHART_SIZES } from './constants';
import { readChartColors } from './theme';
import VChart from './VChart.vue';

// ---------- тестовые данные - в том виде, в каком их отдаёт наш API ----------

const MONTHS = 24;
const HISTORY_DAYS = 60;
const FORECAST_DAYS = 90;
const DAY_MS = 24 * 60 * 60 * 1000;
const CORRIDOR = 'коридор';

/** Выручка по месяцам за 2 года: рост + сезонность (как /api/analysis/overview -> monthly). */
const monthly = Array.from({ length: MONTHS }, (_, index) => {
  const date = new Date(2024, 9 + index, 1);
  const season = 1 + 0.2 * Math.sin(((date.getMonth() - 2) / 12) * 2 * Math.PI);
  return {
    period: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`,
    value: Math.round(17000 * season * (1 + index * 0.008)),
  };
});

/** День -> ISO-дата "2026-10-01". */
function isoDay(start: Date, offset: number): string {
  return new Date(start.getTime() + offset * DAY_MS).toISOString().slice(0, 10);
}

/** Продажи за день: недельная волна (как /api/analysis/forecast -> history, points). */
function dailyValue(offset: number): number {
  return Math.round(620 + 140 * Math.sin((offset / 7) * 2 * Math.PI));
}

const historyStart = new Date(Date.UTC(2026, 7, 2));
const history = Array.from({ length: HISTORY_DAYS }, (_, day) => ({
  period: isoDay(historyStart, day),
  value: dailyValue(day) + ((day * 37) % 90) - 45,
}));
const points = Array.from({ length: FORECAST_DAYS }, (_, day) => {
  const value = dailyValue(HISTORY_DAYS + day);
  const spread = 80 + day * 1.2; // чем дальше, тем шире коридор
  return {
    period: isoDay(historyStart, HISTORY_DAYS + day),
    value,
    lower: value - spread,
    upper: value + spread,
  };
});

/** Топ товаров (как /api/analysis/top -> rows). */
const topRows = [
  { name: 'Пиво Лидское 0.5', value: 137130, share_percent: 27.5 },
  { name: 'Чипсы Lays 140г', value: 75272.4, share_percent: 15.1 },
  { name: 'Вода Боржоми 0.5', value: 70957.2, share_percent: 14.2 },
  { name: 'Пиво Аливария 0.5', value: 63980, share_percent: 12.8 },
  { name: 'Хлеб Нарочанский', value: 57010, share_percent: 11.4 },
];

// ---------- рецепты графиков (на экранах переедут в entities и widgets) ----------

/** Выручка по месяцам: линия с точками, подсказка "сентябрь 2026: 18 740 р.". */
function revenueOption(): EChartsCoreOption {
  return {
    tooltip: {
      // Заголовок - месяц словами ("апрель 2026"), а не как пришёл с сервера ("2026-04")
      formatter: (items: { axisValue: string; marker: string; seriesName: string; value: number }[]) =>
        [
          formatMonth(items[0].axisValue),
          ...items.map(item => `${item.marker}${item.seriesName}: ${formatMoney(item.value)}`),
        ].join('<br>'),
    },
    xAxis: {
      type: 'category',
      data: monthly.map(point => point.period),
      axisLabel: { formatter: (period: string) => formatMonth(period, MONTH_STYLES.short) },
    },
    yAxis: { type: 'value', axisLabel: { formatter: (value: number) => formatMoney(value, '') } },
    series: [
      { name: 'Выручка', type: 'line', data: monthly.map(point => point.value), smooth: true },
    ],
  };
}

/** Факт + прогноз + коридор: коридор - полоса между нижней и верхней границей. */
function forecastOption(): EChartsCoreOption {
  const colors = readChartColors();
  const periods = [...history, ...points].map(point => point.period);
  const pad = (count: number) => Array.from({ length: count }, () => null);
  return {
    legend: { data: ['факт', 'прогноз', CORRIDOR] },
    tooltip: {
      formatter: (items: { seriesName: string; value: unknown; dataIndex: number }[]) => {
        const index = items[0].dataIndex;
        const point = points[index - HISTORY_DAYS];
        // Пустые дни (факт в зоне прогноза и наоборот) не показываем
        const lines = items
          .filter(item => item.seriesName !== CORRIDOR && Number.isFinite(Number(item.value)))
          .map(item => `${item.seriesName}: ${formatMoney(Number(item.value))}`);
        // Коридор - только если он не спрятан в легенде (спрятанные ряды в items не попадают)
        const corridorVisible = items.some(item => item.seriesName === CORRIDOR);
        if (point && corridorVisible) {
          lines.push(`${CORRIDOR}: ${formatMoney(point.lower)} - ${formatMoney(point.upper)}`);
        }
        return [formatDate(periods[index]), ...lines].join('<br>');
      },
    },
    xAxis: {
      type: 'category',
      data: periods,
      axisLabel: { formatter: (period: string) => formatDate(period) },
    },
    yAxis: { type: 'value', axisLabel: { formatter: (value: number) => formatMoney(value, '') } },
    series: [
      {
        name: 'факт',
        type: 'line',
        showSymbol: false,
        data: [...history.map(point => point.value), ...pad(FORECAST_DAYS)],
        markLine: {
          symbol: 'none',
          label: { formatter: 'сегодня', color: colors.textMuted },
          lineStyle: { color: colors.textMuted, type: 'solid' },
          data: [{ xAxis: history.at(-1)?.period }],
        },
      },
      {
        name: 'прогноз',
        type: 'line',
        showSymbol: false,
        lineStyle: { type: 'dashed' },
        data: [...pad(HISTORY_DAYS), ...points.map(point => point.value)],
      },
      // Коридор - два ряда одной стопкой: невидимая нижняя граница + закрашенная ширина.
      // Одно имя у обоих - клик по "коридор" в легенде прячет полосу целиком
      {
        name: CORRIDOR,
        type: 'line',
        stack: CORRIDOR,
        showSymbol: false,
        lineStyle: { opacity: 0 },
        data: [...pad(HISTORY_DAYS), ...points.map(point => point.lower)],
      },
      {
        name: CORRIDOR,
        type: 'line',
        stack: CORRIDOR,
        showSymbol: false,
        lineStyle: { opacity: 0 },
        areaStyle: { color: colors.accentLight, opacity: 0.4 },
        data: [...pad(HISTORY_DAYS), ...points.map(point => point.upper - point.lower)],
      },
    ],
  };
}

/** Топ: горизонтальные столбцы, лидер сверху, подпись "137 130 р. · 27,5 %". */
function topOption(): EChartsCoreOption {
  const rows = [...topRows].reverse(); // ECharts рисует снизу вверх - переворачиваем
  return {
    grid: { right: 140 },
    tooltip: { trigger: 'item', valueFormatter: (value: number) => formatMoney(value) },
    xAxis: { type: 'value', axisLabel: { formatter: (value: number) => formatMoney(value, '') } },
    yAxis: { type: 'category', data: rows.map(row => row.name) },
    series: [
      {
        name: 'Выручка',
        type: 'bar',
        barMaxWidth: 28,
        data: rows.map(row => row.value),
        label: {
          show: true,
          position: 'right',
          formatter: ({ dataIndex }: { dataIndex: number }) =>
            `${formatMoney(rows[dataIndex].value)} · ${formatPercent(rows[dataIndex].share_percent, false)}`,
        },
      },
    ],
  };
}

// ---------- истории ----------

const meta = {
  title: 'shared/ui/VChart',
  component: VChart,
  args: {
    option: {},
    description: 'График',
    size: CHART_SIZES.medium,
    zoomable: false,
    downloadName: undefined,
  },
  argTypes: {
    option: { control: false },
    size: { control: 'inline-radio', options: Object.values(CHART_SIZES) },
  },
} satisfies Meta<typeof VChart>;

export default meta;

type Story = StoryObj<typeof meta>;

/** Выручка по месяцам: наведи на точку - подсказка; колесо мыши или ползунок - приближение. */
export const Revenue: Story = {
  args: {
    option: revenueOption(),
    description: 'Выручка по месяцам за два года: рост с сезонными колебаниями',
    zoomable: true,
    downloadName: 'выручка-по-месяцам',
  },
};

/** Факт, прогноз и коридор. Клик по «коридор» в легенде прячет полосу. */
export const Forecast: Story = {
  args: {
    option: forecastOption(),
    description: 'Продажи по дням: последние 60 дней факта и прогноз на 90 дней с коридором',
    size: CHART_SIZES.large,
    zoomable: true,
    downloadName: 'прогноз',
  },
};

/** Топ товаров: сумма и доля от всей выручки на каждом столбце. */
export const Top: Story = {
  args: {
    option: topOption(),
    description: 'Пять товаров с наибольшей выручкой',
    downloadName: 'топ-товаров',
  },
};
