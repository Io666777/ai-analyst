<template>
  <div :class="$style.MonthDetails">
    <VTabs v-model="view" label="Подробности месяца" :tabs="TABS">
      <VSpinner v-if="isLoading" label="Собираю подробности месяца..." show-label />
      <VAlert v-else-if="error" :variant="ALERT_VARIANTS.error">{{ error }}</VAlert>

      <!-- Товары месяца: что дало выручку -->
      <template v-else-if="view === VIEWS.items && top">
        <p v-if="!top.rows.length" :class="$style.note">В этом месяце продаж нет.</p>
        <div v-else :class="$style.tableWrap">
          <table :class="$style.table">
            <caption :class="$style.caption">Товары за {{ monthTitle }}</caption>
            <thead>
              <tr>
                <th scope="col" :class="$style._number">№</th>
                <th scope="col">{{ capitalize(top.by_label) }}</th>
                <th scope="col" :class="$style._number">Выручка</th>
                <th scope="col" :class="$style._number">Доля месяца</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in top.rows" :key="row.name">
                <td :class="$style._number">{{ index + 1 }}</td>
                <td>
                  <NuxtLink
                    v-if="top.by === ITEM_FIELD"
                    :to="{ path: ROUTES.item, query: { q: row.name } }"
                    :class="$style.link"
                  >
                    {{ row.name }}
                  </NuxtLink>
                  <template v-else>{{ row.name }}</template>
                </td>
                <td :class="$style._number">{{ formatMoney(row.value, top.currency) }}</td>
                <td :class="$style._number">{{ formatPercent(row.share_percent, false) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- По дням: провалы и всплески внутри месяца -->
      <template v-else-if="view === VIEWS.days && daily">
        <div :class="$style.tableWrap">
          <table :class="$style.table">
            <caption :class="$style.caption">Выручка по дням за {{ monthTitle }}</caption>
            <thead>
              <tr>
                <th scope="col">День</th>
                <th scope="col" :class="$style._number">Выручка</th>
                <th scope="col" :class="$style.barHead"><span :class="$style.caption">Сравнение с лучшим днём</span></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="day in daily.days"
                :key="day.period"
                :class="{ [$style._best]: day.value === bestDay, [$style._empty]: !day.value }"
              >
                <td>{{ weekday(day.period) }}, {{ formatDate(day.period) }}</td>
                <td :class="$style._number">{{ formatMoney(day.value, daily.currency) }}</td>
                <td :class="$style.barCell" aria-hidden="true">
                  <span :class="$style.bar" :style="{ width: barWidth(day.value) }" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p :class="$style.note">
          Итого за месяц: {{ formatMoney(daily.total, daily.currency) }}. Жирным - лучший день,
          бледным - дни без продаж
        </p>
      </template>
    </VTabs>
  </div>
</template>

<script setup lang="ts">
/**
 * Подробности месяца из обзора: товары, давшие выручку, и выручка по дням.
 * Оба запроса уходят сразу и параллельно - вкладки переключаются мгновенно.
 *
 * @example
 * <MonthDetails month="2026-09" />
 */
import { computed, ref, watch } from 'vue';
import { NuxtLink } from '#components';
import { fetchDaily, fetchTop } from '~/entities/sale';
import { toApiError } from '~/shared/api';
import { LOCALE, ROUTES, TOP_LIMITS } from '~/shared/config';
import {
  capitalize,
  formatDate,
  formatMoney,
  formatMonth,
  formatPercent,
  parseIsoDate,
  useRequest,
  wholeMonth,
} from '~/shared/lib';
import { ALERT_VARIANTS, type TabOption, VAlert, VSpinner, VTabs } from '~/shared/ui';

const props = defineProps<{
  /** Месяц "2026-09". */
  month: string;
}>();

const VIEWS = { items: 'items', days: 'days' } as const;
const TABS: TabOption[] = [
  { value: VIEWS.items, label: 'Товары месяца' },
  { value: VIEWS.days, label: 'По дням' },
];
/** Поле «товар»: у него есть карточка. */
const ITEM_FIELD = 'object';

const view = ref<string>(VIEWS.items);

const toMessage = (error: unknown) => toApiError(error).message;
const topRequest = useRequest(fetchTop, toMessage);
const dailyRequest = useRequest(fetchDaily, toMessage);

const top = topRequest.data;
const daily = dailyRequest.data;
const isLoading = computed(() => topRequest.isLoading.value || dailyRequest.isLoading.value);
const error = computed(() => topRequest.error.value ?? dailyRequest.error.value);

const monthTitle = computed(() => formatMonth(props.month));
const bestDay = computed(() => Math.max(0, ...(daily.value?.days.map(day => day.value) ?? [])));

const weekdayFormat = new Intl.DateTimeFormat(LOCALE, { weekday: 'short' });

watch(
  () => props.month,
  async month => {
    const date = parseIsoDate(month);
    const { from, to } = wholeMonth(date.getFullYear(), date.getMonth());
    // Два независимых запроса - параллельно, а не друг за другом
    await Promise.all([
      topRequest.run({ top: TOP_LIMITS.max, worst: false, dateFrom: from, dateTo: to }),
      dailyRequest.run(from, to),
    ]);
  },
  { immediate: true },
);

/**
 * День недели коротко: "2026-09-01" → "Вт".
 * @param {string} period - дата.
 * @returns {string} день недели с заглавной буквы.
 */
function weekday(period: string): string {
  return capitalize(weekdayFormat.format(parseIsoDate(period)));
}

/**
 * Длина полоски дня - доля от лучшего дня месяца.
 * @param {number} value - выручка дня.
 * @returns {string} ширина в процентах.
 */
function barWidth(value: number): string {
  return bestDay.value ? `${(value / bestDay.value) * 100}%` : '0%';
}
</script>

<style lang="scss" module>
.MonthDetails {
  display: grid;
  gap: var(--space-3);
}

.note {
  color: var(--base-700);

  @include text(small);
}

// Таблица шире экрана телефона - прокручивается сама, а не вся страница
.tableWrap {
  max-height: 28rem;
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
    position: sticky; // шапка остаётся видна при прокрутке длинного списка
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

._best {
  font-weight: 600;
}

._empty {
  color: var(--base-500);
}

.barHead {
  width: 40%;
}

.barCell {
  vertical-align: middle;
}

// Полоска - как маленький столбик: провалы и всплески видны без графика
.bar {
  display: block;
  height: 0.5rem;
  min-width: 1px;
  background: var(--primary-300);
  border-radius: var(--radius-small);
}

.caption {
  @include visually-hidden;
}

.link {
  color: var(--primary-600);

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: var(--focus-width);
  }
}
</style>
