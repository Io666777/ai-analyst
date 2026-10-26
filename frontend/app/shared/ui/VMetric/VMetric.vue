<template>
  <div :class="$style.VMetric">
    <p :class="$style.label">{{ label }}</p>
    <p :class="$style.value">{{ formattedValue }}</p>

    <p v-if="change !== undefined" :class="changeClassList">
      <span v-if="!isUnknown" aria-hidden="true">{{ TREND_ARROWS[trend] }}</span>
      <span aria-hidden="true">{{ formatPercent(change) }}</span>
      <span v-if="changeLabel" aria-hidden="true">{{ changeLabel }}</span>
      <!-- Для диктора - словами: стрелки и знаки он прочитает невнятно -->
      <span :class="$style.hidden">{{ spokenChange }}</span>
    </p>

    <p v-if="hint" :class="$style.hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
/**
 * Крупная цифра с подписью и изменением: стрелка, рост - зелёным, падение - красным.
 * Значение форматируется само: деньги, число или процент.
 *
 * @example
 * <VMetric label="Выручка: сентябрь 2026" :value="18740" currency="р."
 *          :change="-7.6" change-label="к прошлому месяцу" />
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, useCssModule } from 'vue';
import { DEFAULT_CURRENCY } from '~/shared/config';
import { formatMoney, formatNumber, formatPercent, TRENDS, type Trend, trendOf } from '~/shared/lib';
import { METRIC_FORMATS, type MetricFormat } from './constants';

const props = withDefaults(
  defineProps<{
    /** Что это за цифра. */
    label: string;
    /** Значение. */
    value: number;
    /** Как показать значение. */
    format?: MetricFormat;
    /** Валюта - для format="money". */
    currency?: string;
    /** Изменение в процентах (-7.6). null - процент не посчитать (было 0); не задано - не показывать. */
    change?: number | null;
    /** К чему изменение: "к прошлому месяцу". */
    changeLabel?: string;
    /** Пояснение мелким шрифтом под цифрой. */
    hint?: string;
  }>(),
  {
    format: METRIC_FORMATS.money,
    currency: DEFAULT_CURRENCY,
    change: undefined,
    changeLabel: undefined,
    hint: undefined,
  },
);

const TREND_ARROWS: Record<Trend, string> = {
  [TRENDS.up]: '↑',
  [TRENDS.down]: '↓',
  [TRENDS.flat]: '→',
};

const TREND_WORDS: Record<Trend, string> = {
  [TRENDS.up]: 'рост на',
  [TRENDS.down]: 'снижение на',
  [TRENDS.flat]: 'без изменений',
};

const VALUE_FORMATTERS: Record<MetricFormat, (value: number) => string> = {
  [METRIC_FORMATS.money]: value => formatMoney(value, props.currency),
  [METRIC_FORMATS.number]: value => formatNumber(value),
  [METRIC_FORMATS.percent]: value => formatPercent(value, false),
};

const style = useCssModule();

const formattedValue = computed(() => VALUE_FORMATTERS[props.format](props.value));
const trend = computed(() => trendOf(props.change ?? null));
// null - не "без изменений", а "не посчитать": в прошлом периоде было 0
const isUnknown = computed(() => props.change === null);

const changeClassList = computed(() => [style.change, style[`_${trend.value}`]]);

const spokenChange = computed(() => {
  if (isUnknown.value) return 'изменение не посчитать: в прошлом периоде продаж не было';
  if (trend.value === TRENDS.flat) return TREND_WORDS.flat;
  const percent = formatPercent(Math.abs(props.change as number), false);
  return [TREND_WORDS[trend.value], percent, props.changeLabel].filter(Boolean).join(' ');
});
</script>

<style lang="scss" module>
.VMetric {
  display: grid;
  gap: var(--space-1);
  align-content: start;
}

.label {
  color: var(--base-700);

  @include text(small);
}

.value {
  color: var(--base-900);
  font-variant-numeric: tabular-nums; // цифры одной ширины - не "прыгают" при обновлении

  @include text(metric);

  @include respond-to(mobile) {
    @include text(h1);
  }
}

.change {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  justify-self: start;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-small);

  @include text(small);

  &._up {
    color: var(--success-700);
    background: var(--success-100);
  }

  &._down {
    color: var(--error-500);
    background: var(--error-100);
  }

  &._flat {
    color: var(--base-700);
    background: var(--base-100);
  }
}

.hint {
  color: var(--base-500);

  @include text(caption);
}

.hidden {
  @include visually-hidden;
}
</style>
