<template>
  <figure :class="classList" role="img" :aria-label="description">
    <div ref="container" :class="$style.canvas" />
  </figure>
</template>

<script setup lang="ts">
/**
 * Интерактивный график на ECharts: подсказки при наведении, легенда (клик прячет ряд),
 * приближение (zoomable) и кнопка «скачать PNG» (downloadName).
 * Код ECharts загружается лениво - только когда график появился на странице.
 * Подстраивается под размер блока и освобождает память при уходе со страницы.
 *
 * @example
 * <VChart :option="revenueOption" description="Выручка по месяцам" zoomable download-name="выручка" />
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import type { ECharts, EChartsCoreOption } from 'echarts/core';
import {
  computed,
  onBeforeUnmount,
  onMounted,
  shallowRef,
  useCssModule,
  useTemplateRef,
  watch,
} from 'vue';
import { CHART_SIZES, type ChartSize } from './constants';
import { baseOption, readChartColors, toolboxOption, zoomOption } from './theme';

const props = withDefaults(
  defineProps<{
    /** Настройки графика ECharts: ряды, оси, подсказки. Общий вид добавляется сам. */
    option: EChartsCoreOption;
    /** Что показывает график - словами, для экранного диктора. */
    description: string;
    /** Высота. */
    size?: ChartSize;
    /** Приближение: колесо мыши, щипок, ползунок снизу и кнопка «сбросить». */
    zoomable?: boolean;
    /** Имя файла для кнопки «скачать PNG»; не задано - кнопки нет. */
    downloadName?: string;
    /**
     * Можно выбрать точку кликом: событие select с номером. У линий и столбцов клик
     * засчитывается по всей колонке (по точке на линии попасть трудно), у кольца - по сектору.
     */
    selectable?: boolean;
  }>(),
  {
    size: CHART_SIZES.medium,
    zoomable: false,
    downloadName: undefined,
    selectable: false,
  },
);

const emit = defineEmits<{
  /** Выбрана точка (selectable): номер в данных - колонка оси или сектор. */
  select: [index: number];
}>();

const style = useCssModule();
const container = useTemplateRef<HTMLDivElement>('container');
const chart = shallowRef<ECharts | null>(null);

let resizeObserver: ResizeObserver | null = null;
let isUnmounted = false;

const classList = computed(() => [style.VChart, style[`_${props.size}`]]);

/** Рисует график заново: общий вид + приближение + кнопки + настройки из пропса. */
function render(): void {
  if (!chart.value) return;
  const colors = readChartColors();
  chart.value.clear();
  chart.value.setOption(baseOption(colors));
  if (props.zoomable) chart.value.setOption(zoomOption(colors));
  chart.value.setOption(
    toolboxOption({ zoomable: props.zoomable, fileName: props.downloadName ?? null }),
  );
  chart.value.setOption(props.option);
}

/**
 * Клики для выбора точки: по сектору кольца - сам сектор, по области с осями - колонка под курсором.
 * @param {ECharts} instance - график.
 */
function listenSelect(instance: ECharts): void {
  // У кольца нет колонок: выбор - только клик по сектору
  const isPie = () =>
    (instance.getOption().series as { type?: string }[] | undefined)?.[0]?.type === 'pie';

  instance.on('click', params => {
    if (params.componentSubType === 'pie') emit('select', params.dataIndex);
  });
  instance.getZr().on('click', ({ offsetX, offsetY }) => {
    const point = [offsetX, offsetY];
    if (isPie() || !instance.containPixel('grid', point)) return; // мимо осей: легенда, кнопки
    const [index] = instance.convertFromPixel({ gridIndex: 0 }, point) as number[];
    if (Number.isFinite(index)) emit('select', Math.round(index));
  });
  // Курсор-рука над областью с осями: видно, что сюда можно нажать
  instance.getZr().on('mousemove', ({ offsetX, offsetY }) => {
    if (isPie()) return; // над сектором рука и так появляется сама
    const inside = instance.containPixel('grid', [offsetX, offsetY]);
    instance.getZr().setCursorStyle(inside ? 'pointer' : 'default');
  });
}

onMounted(async () => {
  // Ленивая загрузка: код ECharts скачивается только сейчас, когда график появился
  const { echarts, ECHARTS_LOCALE } = await import('./echarts');
  if (isUnmounted || !container.value) return; // ушли со страницы, пока грузилось

  chart.value = echarts.init(container.value, null, { locale: ECHARTS_LOCALE });
  render();
  if (props.selectable) listenSelect(chart.value);
  resizeObserver = new ResizeObserver(() => chart.value?.resize());
  resizeObserver.observe(container.value);
});

watch(() => [props.option, props.zoomable, props.downloadName], render, { deep: true });

// Освобождаем память: следим за размером и держим холст, только пока график на странице
onBeforeUnmount(() => {
  isUnmounted = true;
  resizeObserver?.disconnect();
  chart.value?.dispose();
});
</script>

<style lang="scss" module>
.VChart {
  margin: 0;
  min-width: 0;

  &._small {
    --chart-height: 14rem;
  }

  &._medium {
    --chart-height: 20rem;
  }

  &._large {
    --chart-height: 26rem;
  }

  @include respond-to(mobile) {
    &._large {
      --chart-height: 22rem;
    }
  }
}

.canvas {
  width: 100%;
  height: var(--chart-height);
  border-radius: var(--radius);
}
</style>
