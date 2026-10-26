<template>
  <div :class="$style.ItemMonth">
    <VSpinner v-if="isLoading && !data" label="Собираю месяц товара..." show-label />
    <VAlert v-else-if="error" :variant="ALERT_VARIANTS.error">{{ error }}</VAlert>

    <template v-else-if="data">
      <p :class="$style.summary">
        За месяц: <strong>{{ formatMoney(data.total, data.currency) }}</strong>
        <template v-if="data.quantity !== null && data.quantity !== undefined">
          · продано {{ formatNumber(data.quantity) }} шт.
        </template>
        · дней с продажами: {{ soldDays }} из {{ data.days.length }}
      </p>
      <p :class="$style.note">Нажмите на день - покажу, какое место товар занял в продажах дня.</p>

      <div :class="$style.tableWrap">
        <table :class="$style.table">
          <caption :class="$style.caption">{{ data.name }} по дням</caption>
          <thead>
            <tr>
              <th scope="col">День</th>
              <th v-if="hasQuantity" scope="col" :class="$style._number">Продано, шт.</th>
              <th scope="col" :class="$style._number">Выручка</th>
              <th v-if="data.has_executors" scope="col">Кто продавал</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="day in data.days"
              :key="day.period"
              :class="{ [$style._selected]: day.period === selectedDay, [$style._empty]: !day.amount }"
            >
              <td>
                <!-- Кнопка, а не клик по строке: так день выбирается и с клавиатуры -->
                <button
                  type="button"
                  :class="$style.dayButton"
                  :aria-pressed="day.period === selectedDay"
                  :disabled="!day.amount"
                  @click="selectDay(day.period)"
                >
                  {{ weekday(day.period) }}, {{ formatDate(day.period) }}
                </button>
              </td>
              <td v-if="hasQuantity" :class="$style._number">{{ formatNumber(day.quantity ?? 0) }}</td>
              <td :class="$style._number">{{ formatMoney(day.amount, data.currency) }}</td>
              <td v-if="data.has_executors">{{ day.executors.join(', ') || EMPTY_VALUE }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <section v-if="selectedDay" ref="dayCard" :class="$style.day" :aria-label="`Продажи ${formatDate(selectedDay)}`">
        <h3 :class="$style.dayTitle">{{ weekday(selectedDay) }}, {{ formatDate(selectedDay) }}: место в продажах дня</h3>
        <VSpinner v-if="dayRequest.isLoading.value" label="Считаю продажи дня..." show-label />
        <VAlert v-else-if="dayRequest.error.value" :variant="ALERT_VARIANTS.error">
          {{ dayRequest.error.value }}
        </VAlert>
        <template v-else-if="dayTop && selectedItemDay">
          <p :class="$style.summary">
            {{ data.name }}: <strong>{{ formatMoney(selectedItemDay.amount, data.currency) }}</strong>
            из {{ formatMoney(dayTop.total, data.currency) }} за день
            ({{ formatPercent(itemShare, false) }}){{ placeText }}
          </p>
          <VChart
            :option="dayOption"
            :description="`Доли товаров в выручке ${formatDate(selectedDay)}: ${data.name} - ${formatPercent(itemShare, false)}`"
            :size="CHART_SIZES.medium"
            :download-name="`день-${selectedDay}`"
          />
        </template>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Месяц товара по дням: штуки, выручка, кто продавал. Клик по дню - кольцо:
 * какое место товар занял во всей выручке этого дня.
 *
 * @example
 * <ItemMonth query="Пиво Лидское 0.5" :all="false" :items="['Пиво Лидское 0.5']" month="2026-09" />
 */
import { computed, nextTick, ref, useTemplateRef, watch } from 'vue';
import { fetchTop } from '~/entities/sale';
import { toApiError } from '~/shared/api';
import { EMPTY_VALUE, LOCALE, TOP_LIMITS } from '~/shared/config';
import {
  capitalize,
  formatDate,
  formatMoney,
  formatNumber,
  formatPercent,
  parseIsoDate,
  useRequest,
  wholeMonth,
} from '~/shared/lib';
import { ALERT_VARIANTS, CHART_SIZES, readChartPalette, VAlert, VChart, VSpinner } from '~/shared/ui';
import { fetchItemDays } from '../api/item-api';
import { dayShareOption, daySlices } from '../lib/day-share-chart';

const props = defineProps<{
  /** Название товара, а для all - запрос. */
  query: string;
  /** Все подходящие товары вместе. */
  all: boolean;
  /** Какие товары вошли - чтобы выделить их на кольце дня. */
  items: readonly string[];
  /** Месяц "2026-09". */
  month: string;
}>();

const toMessage = (error: unknown) => toApiError(error).message;
const { data, isLoading, error, run } = useRequest(fetchItemDays, toMessage);
const dayRequest = useRequest(fetchTop, toMessage);
const dayTop = dayRequest.data;

const selectedDay = ref<string | null>(null);
const dayCard = useTemplateRef<HTMLElement>('dayCard');
const palette = readChartPalette();
const weekdayFormat = new Intl.DateTimeFormat(LOCALE, { weekday: 'short' });

const hasQuantity = computed(() => data.value?.quantity !== null && data.value?.quantity !== undefined);
const soldDays = computed(() => data.value?.days.filter(day => day.amount > 0).length ?? 0);
const selectedItemDay = computed(() =>
  data.value?.days.find(day => day.period === selectedDay.value),
);
const itemShare = computed(() =>
  dayTop.value?.total ? ((selectedItemDay.value?.amount ?? 0) / dayTop.value.total) * 100 : 0,
);

// Место товара среди товаров дня: «2-е место из 7» - понятнее процента
const placeText = computed(() => {
  if (!dayTop.value || props.items.length !== 1) return '';
  const place = dayTop.value.rows.findIndex(row => row.name === props.items[0]);
  return place >= 0 ? ` - ${place + 1}-е место из ${dayTop.value.rows.length}` : '';
});

const dayOption = computed(() =>
  data.value && dayTop.value && selectedItemDay.value
    ? dayShareOption(
        daySlices({
          items: props.items,
          itemValue: selectedItemDay.value.amount,
          top: dayTop.value.rows,
          total: dayTop.value.total,
        }),
        data.value.currency,
        palette,
      )
    : {},
);

watch(
  () => [props.query, props.all, props.month] as const,
  ([query, all, month]) => {
    selectedDay.value = null;
    const date = parseIsoDate(month);
    const { from, to } = wholeMonth(date.getFullYear(), date.getMonth());
    run({ query, all, dateFrom: from, dateTo: to });
  },
  { immediate: true },
);

/**
 * Выбрать день: топ товаров за этот день - и прокрутить к кольцу.
 * @param {string} period - день "2026-09-15".
 */
async function selectDay(period: string): Promise<void> {
  selectedDay.value = period;
  await dayRequest.run({ top: TOP_LIMITS.max, worst: false, dateFrom: period, dateTo: period });
  await nextTick();
  dayCard.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * День недели коротко: "2026-09-01" → "Вт".
 * @param {string} period - дата.
 * @returns {string} день недели с заглавной буквы.
 */
function weekday(period: string): string {
  return capitalize(weekdayFormat.format(parseIsoDate(period)));
}
</script>

<style lang="scss" module>
.ItemMonth {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-3);
}

.summary {
  color: var(--base-900);

  @include text(small);
}

.note {
  color: var(--base-700);

  @include text(small);
}

// Длинный месяц прокручивается внутри, шапка таблицы остаётся видна
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
    padding: var(--space-1) var(--space-3);
    text-align: left;
    border-bottom: var(--border-width) solid var(--base-100);
  }

  th {
    position: sticky;
    top: 0;
    padding-block: var(--space-2);
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

._selected {
  background: var(--primary-100);
}

._empty {
  color: var(--base-500);
}

.dayButton {
  padding: var(--space-1) 0;
  color: var(--primary-600);
  text-align: left;
  white-space: nowrap;
  cursor: pointer;
  background: none;
  border: 0;
  text-decoration: underline;

  @include text(small);

  &:disabled {
    color: inherit;
    cursor: default;
    text-decoration: none;
  }

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: var(--focus-width);
  }
}

.day {
  display: grid;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: var(--border-width) solid var(--base-100);
}

.dayTitle {
  @include text(h3);
}

.caption {
  @include visually-hidden;
}
</style>
