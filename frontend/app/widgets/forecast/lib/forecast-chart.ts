// Рецепт графика «факт + прогноз + коридор»: факт - сплошной линией, прогноз - пунктиром,
// коридор - полосой (в 8 случаях из 10 реальность внутри). Черта «сегодня» - где кончились данные
import type { DeepReadonly } from 'vue';
import type { ForecastPoint, SeriesPoint } from '~/shared/api';
import { formatDate, formatMoney } from '~/shared/lib';
import type { ChartColors, ChartOption } from '~/shared/ui';

const SERIES = { fact: 'факт', forecast: 'прогноз', corridor: 'коридор' } as const;
const CORRIDOR_OPACITY = 0.4;

interface TooltipItem {
  seriesName: string;
  value: unknown;
  dataIndex: number;
}

/**
 * Пустые места ряда: факт в зоне прогноза и наоборот.
 * @param {number} count - сколько.
 * @returns {null[]} пустые значения - ECharts их не рисует.
 */
function gaps(count: number): null[] {
  return Array.from({ length: count }, () => null);
}

/**
 * Настройки ECharts для прогноза.
 * @param {object} data - данные графика.
 * @param {DeepReadonly<SeriesPoint[]>} data.history - конец истории по дням.
 * @param {DeepReadonly<ForecastPoint[]>} data.points - прогноз по дням.
 * @param {string} data.currency - валюта.
 * @param {ChartColors} colors - цвета графиков (readChartColors).
 * @returns {ChartOption} настройки для VChart.
 */
export function forecastChartOption(
  data: {
    history: DeepReadonly<SeriesPoint[]>;
    points: DeepReadonly<ForecastPoint[]>;
    currency: string;
  },
  colors: ChartColors,
): ChartOption {
  const { history, points, currency } = data;
  const periods = [...history, ...points].map(point => point.period);
  // Коридор считают не все модели: у простого прогноза его нет
  const hasCorridor = points.some(point => point.lower !== null && point.upper !== null);
  const money = (value: number) => formatMoney(value, currency);

  const corridorSeries = hasCorridor
    ? [
        // Два ряда одной стопкой: невидимая нижняя граница + закрашенная ширина.
        // Одно имя у обоих - клик по «коридор» в легенде прячет полосу целиком
        {
          name: SERIES.corridor,
          type: 'line',
          stack: SERIES.corridor,
          showSymbol: false,
          lineStyle: { opacity: 0 },
          data: [...gaps(history.length), ...points.map(point => point.lower)],
        },
        {
          name: SERIES.corridor,
          type: 'line',
          stack: SERIES.corridor,
          showSymbol: false,
          lineStyle: { opacity: 0 },
          areaStyle: { color: colors.accentLight, opacity: CORRIDOR_OPACITY },
          data: [
            ...gaps(history.length),
            ...points.map(point => (point.upper ?? 0) - (point.lower ?? 0)),
          ],
        },
      ]
    : [];

  return {
    legend: {
      data: hasCorridor
        ? [SERIES.fact, SERIES.forecast, SERIES.corridor]
        : [SERIES.fact, SERIES.forecast],
    },
    tooltip: {
      formatter: (items: TooltipItem[]) => {
        const index = items[0].dataIndex;
        const point = points[index - history.length];
        // Пустые дни (факт в зоне прогноза и наоборот) не показываем
        const lines = items
          .filter(item => item.seriesName !== SERIES.corridor && Number.isFinite(Number(item.value)))
          .map(item => `${item.seriesName}: ${money(Number(item.value))}`);
        // Коридор - только если он не спрятан в легенде (спрятанные ряды в items не попадают)
        const corridorShown = items.some(item => item.seriesName === SERIES.corridor);
        if (point && corridorShown && point.lower !== null && point.upper !== null) {
          lines.push(`${SERIES.corridor}: ${money(point.lower)} - ${money(point.upper)}`);
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
        name: SERIES.fact,
        type: 'line',
        showSymbol: false,
        data: [...history.map(point => point.value), ...gaps(points.length)],
        markLine: {
          symbol: 'none',
          label: { formatter: 'конец данных', color: colors.textMuted },
          lineStyle: { color: colors.textMuted, type: 'solid' },
          data: [{ xAxis: history.at(-1)?.period }],
        },
      },
      {
        name: SERIES.forecast,
        type: 'line',
        showSymbol: false,
        lineStyle: { type: 'dashed' },
        data: [...gaps(history.length), ...points.map(point => point.value)],
      },
      ...corridorSeries,
    ],
  };
}
