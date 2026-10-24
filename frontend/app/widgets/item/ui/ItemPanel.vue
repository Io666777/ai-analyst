<template>
  <div :class="$style.ItemPanel" :aria-busy="isLoading">
    <VSpinner v-if="isLoading && !data" label="Собираю данные о товаре..." show-label />

    <VAlert v-else-if="error" :variant="ALERT_VARIANTS.error" title="Не получилось открыть товар">
      {{ error }}
    </VAlert>

    <template v-else-if="data">
      <VCard :title="data.name">
        <p :class="$style.note">
          Продавался с {{ formatDate(data.first_sale) }} по {{ formatDate(data.last_sale) }}
        </p>
        <p v-if="data.items.length > 1" :class="$style.note">
          Вместе: {{ data.items.join(', ') }}
        </p>

        <div :class="$style.metrics">
          <VMetric
            label="Выручка за весь период"
            :value="data.amount"
            :currency="data.currency"
          />
          <VMetric
            label="Доля от всей выручки"
            :value="data.share_percent"
            :format="METRIC_FORMATS.percent"
          />
          <VMetric
            v-if="data.quantity !== null && data.quantity !== undefined"
            label="Продано, штук"
            :value="data.quantity"
            :format="METRIC_FORMATS.number"
          />
          <VMetric
            v-if="data.last_month"
            :label="`Выручка: ${data.last_month.month}`"
            :value="data.last_month.after"
            :currency="data.currency"
            :change="data.last_month.change_percent"
            change-label="к прошлому месяцу"
            :hint="`${capitalize(data.last_month.previous_month)}: ${formatMoney(data.last_month.before, data.currency)}`"
          />
        </div>
      </VCard>

      <VCard title="Выручка по месяцам">
        <template v-if="data.monthly.length">
          <p :class="$style.note">
            Нажмите на месяц - покажу продажи по дням. Месяцы - по всем данным: месяц без продаж
            этого товара показан нулём.
          </p>
          <RevenueChart
            :points="data.monthly"
            :currency="data.currency"
            :download-name="`выручка-${data.name}`"
            selectable
            :selected="month"
            @select="openMonth"
          />
          <!-- То же без мыши: по холсту графика не пройти клавиатурой, по списку - можно -->
          <VSelect
            v-model="monthModel"
            :class="$style.monthSelect"
            label="Месяц по дням"
            placeholder="Выберите месяц"
            :options="monthOptions"
          />
        </template>
        <p v-else :class="$style.note">Нет ни одного полного месяца - графику не из чего строиться.</p>
      </VCard>

      <section v-if="month" ref="details" :class="$style.details">
        <VCard :title="`${capitalize(formatMonth(month))}: ${data.name}`">
          <template #actions>
            <VButton :variant="BUTTON_VARIANTS.ghost" :size="BUTTON_SIZES.small" @click="openMonth('')">
              Скрыть
            </VButton>
          </template>
          <ItemMonth :query="query" :all="all" :items="data.items" :month="month" />
        </VCard>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Карточка товара (или нескольких вместе): цифры и выручка по месяцам.
 * Поменялся товар - данные загружаются заново.
 *
 * @example
 * <ItemPanel query="Пиво Лидское 0.5" :all="false" />
 */
import { computed, nextTick, useTemplateRef, watch } from 'vue';
import { RevenueChart } from '~/entities/revenue';
import { useSessionState } from '~/entities/session';
import { toApiError } from '~/shared/api';
import { capitalize, formatDate, formatMoney, formatMonth, useRequest } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_SIZES,
  BUTTON_VARIANTS,
  METRIC_FORMATS,
  type SelectOption,
  VAlert,
  VButton,
  VCard,
  VMetric,
  VSelect,
  VSpinner,
} from '~/shared/ui';
import { fetchItem } from '../api/item-api';
import ItemMonth from './ItemMonth.vue';

const props = defineProps<{
  /** Название товара, а для all - запрос. */
  query: string;
  /** Все подходящие товары вместе. */
  all: boolean;
}>();

const { data, isLoading, error, run } = useRequest(fetchItem, err => toApiError(err).message);

// Открытый месяц запоминается вместе с товаром: открыли другой товар - месяц не переносится
const opened = useSessionState<{ item: string; month: string } | null>('item-month', () => null);
const itemKey = computed(() => `${props.query}|${props.all}`);
const month = computed(() => (opened.value?.item === itemKey.value ? opened.value.month : null));
const details = useTemplateRef<HTMLElement>('details');

// Список выбора: свежие месяцы сверху
const monthOptions = computed<SelectOption[]>(() =>
  [...(data.value?.monthly ?? [])]
    .reverse()
    .map(point => ({ value: point.period, label: capitalize(formatMonth(point.period)) })),
);

const monthModel = computed({
  get: () => month.value ?? '',
  set: (value: string) => openMonth(value),
});

/**
 * Открыть месяц по дням и прокрутить к нему; пустая строка - закрыть.
 * @param {string} period - месяц "2026-09".
 */
async function openMonth(period: string): Promise<void> {
  opened.value = period ? { item: itemKey.value, month: period } : null;
  if (!period) return;
  await nextTick();
  details.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

watch(
  () => [props.query, props.all] as const,
  ([query, all]) => run(query, all),
  { immediate: true },
);
</script>

<style lang="scss" module>
.ItemPanel {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-5);
}

.monthSelect {
  max-width: 18rem;
  margin-top: var(--space-3);
}

// Прокрутка к месяцу - с отступом от края окна
.details {
  scroll-margin-top: var(--space-4);
}

.note {
  color: var(--base-700);

  @include text(small);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: var(--space-5);
}
</style>
