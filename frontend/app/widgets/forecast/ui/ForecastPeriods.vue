<template>
  <VTabs v-model="view" label="Прогноз крупнее, чем по дням" :tabs="TABS">
    <div :class="$style.tableWrap">
      <table :class="$style.table">
        <caption :class="$style.caption">Прогноз {{ view === VIEWS.weeks ? 'по неделям' : 'по месяцам' }}</caption>
        <thead>
          <tr>
            <th scope="col">{{ view === VIEWS.weeks ? 'Неделя' : 'Месяц' }}</th>
            <th scope="col" :class="$style._number">Ожидаемая выручка</th>
            <th v-if="hasCorridor" scope="col" :class="$style._number">Скорее всего</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="period in periods" :key="period.date_from">
            <td>
              {{ periodLabel(period) }}
              <span v-if="isPartial(period)" :class="$style.partial">({{ pluralize(daysIn(period), DAY_FORMS) }})</span>
            </td>
            <td :class="$style._number">{{ formatMoney(period.value, currency) }}</td>
            <td v-if="hasCorridor" :class="[$style._number, $style.corridor]">
              {{ formatMoney(period.lower ?? 0, currency) }} - {{ formatMoney(period.upper ?? 0, currency) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </VTabs>
</template>

<script setup lang="ts">
/**
 * Прогноз по неделям и месяцам: сколько ждать и в каких пределах.
 * Крайние периоды бывают неполными - рядом число дней, чтобы не путать с полной неделей.
 *
 * @example
 * <ForecastPeriods :weeks="forecast.weeks" :months="forecast.months" currency="р." />
 */
import type { DeepReadonly } from 'vue';
import { computed, ref } from 'vue';
import type { ForecastPeriod } from '~/shared/api';
import {
  capitalize,
  formatDate,
  formatMoney,
  formatMonth,
  parseIsoDate,
  pluralize,
  type WordForms,
} from '~/shared/lib';
import { type TabOption, VTabs } from '~/shared/ui';

const props = defineProps<{
  weeks: DeepReadonly<ForecastPeriod[]>;
  months: DeepReadonly<ForecastPeriod[]>;
  currency: string;
}>();

const VIEWS = { weeks: 'weeks', months: 'months' } as const;
const TABS: TabOption[] = [
  { value: VIEWS.weeks, label: 'По неделям' },
  { value: VIEWS.months, label: 'По месяцам' },
];
const DAY_FORMS: WordForms = { one: 'день', few: 'дня', many: 'дней' };
const WEEK_DAYS = 7;
const DAY_MS = 24 * 60 * 60 * 1000;

const view = ref<string>(VIEWS.weeks);

const periods = computed(() => (view.value === VIEWS.weeks ? props.weeks : props.months));
const hasCorridor = computed(() => periods.value.some(period => period.lower !== null));

/**
 * Сколько дней в периоде, включая оба края.
 * @param {DeepReadonly<ForecastPeriod>} period - период.
 * @returns {number} дней.
 */
function daysIn(period: DeepReadonly<ForecastPeriod>): number {
  const from = parseIsoDate(period.date_from).getTime();
  const to = parseIsoDate(period.date_to).getTime();
  return Math.round((to - from) / DAY_MS) + 1;
}

/**
 * Неполный ли период: неделя меньше 7 дней, месяц - не с первого по последнее число.
 * @param {DeepReadonly<ForecastPeriod>} period - период.
 * @returns {boolean} да - неполный.
 */
function isPartial(period: DeepReadonly<ForecastPeriod>): boolean {
  if (view.value === VIEWS.weeks) return daysIn(period) < WEEK_DAYS;
  const from = parseIsoDate(period.date_from);
  const to = parseIsoDate(period.date_to);
  const lastDay = new Date(to.getFullYear(), to.getMonth() + 1, 0).getDate();
  return from.getDate() !== 1 || to.getDate() !== lastDay;
}

/**
 * Подпись периода: неделя - датами, месяц - словом.
 * @param {DeepReadonly<ForecastPeriod>} period - период.
 * @returns {string} «05.10.2026 - 11.10.2026» или «Ноябрь 2026».
 */
function periodLabel(period: DeepReadonly<ForecastPeriod>): string {
  if (view.value === VIEWS.months) return capitalize(formatMonth(period.date_from));
  return `${formatDate(period.date_from)} - ${formatDate(period.date_to)}`;
}
</script>

<style lang="scss" module>
.tableWrap {
  max-height: 24rem;
  overflow: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;

  @include text(small);

  th,
  td {
    padding: var(--space-2) var(--space-3);
    text-align: left;
    border-bottom: var(--border-width) solid var(--base-100);
  }

  th {
    position: sticky;
    top: 0;
    color: var(--base-700);
    background: var(--white);
    font-weight: 600;
  }

  ._number {
    text-align: right;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }
}

.partial,
.corridor {
  color: var(--base-500);
}

.caption {
  @include visually-hidden;
}
</style>
