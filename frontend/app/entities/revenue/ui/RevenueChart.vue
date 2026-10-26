<template>
  <VChart
    :option="option"
    :description="description"
    :size="size"
    zoomable
    :selectable="selectable"
    :download-name="downloadName"
    @select="handleSelect"
  />
</template>

<script setup lang="ts">
/**
 * Выручка по месяцам: наведение - подсказка, колесо мыши или ползунок - приближение,
 * кнопка - скачать PNG. selectable - клик по месяцу выбирает его (событие select).
 *
 * @example
 * <RevenueChart :points="overview.monthly" :currency="overview.currency" />
 */
import type { DeepReadonly } from 'vue';
import { computed } from 'vue';
import type { SeriesPoint } from '~/shared/api';
import { formatMonth } from '~/shared/lib';
import { CHART_SIZES, type ChartSize, readChartColors, VChart } from '~/shared/ui';
import { revenueChartOption } from '../lib/revenue-chart';

const props = withDefaults(
  defineProps<{
    /** Месяцы и выручка - как отдаёт сервер. */
    points: DeepReadonly<SeriesPoint[]>;
    /** Как подписывать суммы. */
    currency: string;
    /** Высота графика. */
    size?: ChartSize;
    /** Имя файла для «скачать PNG». */
    downloadName?: string;
    /** Можно выбрать месяц кликом. */
    selectable?: boolean;
    /** Выбранный месяц "2026-09" - отмечен вертикальной чертой. */
    selected?: string | null;
  }>(),
  {
    size: CHART_SIZES.medium,
    downloadName: 'выручка-по-месяцам',
    selectable: false,
    selected: null,
  },
);

const emit = defineEmits<{
  /** Выбран месяц (selectable): "2026-09". */
  select: [period: string];
}>();

const option = computed(() =>
  revenueChartOption(
    props.points,
    props.currency,
    props.selected ? { period: props.selected, color: readChartColors().primary } : undefined,
  ),
);

// Для экранного диктора: картинку он не прочитает, а период - да
const description = computed(() => {
  const first = props.points[0];
  const last = props.points.at(-1);
  if (!first || !last) return 'Выручка по месяцам: данных нет';
  return `Выручка по месяцам с ${formatMonth(first.period)} по ${formatMonth(last.period)}`;
});

/**
 * Клик по колонке месяца.
 * @param {number} index - номер месяца на оси.
 */
function handleSelect(index: number): void {
  const point = props.points[index];
  if (point) emit('select', point.period);
}
</script>
