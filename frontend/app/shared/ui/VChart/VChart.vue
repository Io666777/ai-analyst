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
  }>(),
  {
    size: CHART_SIZES.medium,
    zoomable: false,
    downloadName: undefined,
  },
);

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

onMounted(async () => {
  // Ленивая загрузка: код ECharts скачивается только сейчас, когда график появился
  const { echarts, ECHARTS_LOCALE } = await import('./echarts');
  if (isUnmounted || !container.value) return; // ушли со страницы, пока грузилось

  chart.value = echarts.init(container.value, null, { locale: ECHARTS_LOCALE });
  render();
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
