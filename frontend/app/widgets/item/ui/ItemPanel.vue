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
        <RevenueChart
          v-if="data.monthly.length"
          :points="data.monthly"
          :currency="data.currency"
          :download-name="`выручка-${data.name}`"
        />
        <p v-else :class="$style.note">Нет ни одного полного месяца - графику не из чего строиться.</p>
        <p v-if="data.monthly.length" :class="$style.note">
          Месяцы - по всем данным: месяц без продаж этого товара показан нулём.
        </p>
      </VCard>
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
import { watch } from 'vue';
import { RevenueChart } from '~/entities/revenue';
import { toApiError } from '~/shared/api';
import { capitalize, formatDate, formatMoney, useRequest } from '~/shared/lib';
import { ALERT_VARIANTS, METRIC_FORMATS, VAlert, VCard, VMetric, VSpinner } from '~/shared/ui';
import { fetchItem } from '../api/item-api';

const props = defineProps<{
  /** Название товара, а для all - запрос. */
  query: string;
  /** Все подходящие товары вместе. */
  all: boolean;
}>();

const { data, isLoading, error, run } = useRequest(fetchItem, err => toApiError(err).message);

watch(
  () => [props.query, props.all] as const,
  ([query, all]) => run(query, all),
  { immediate: true },
);
</script>

<style lang="scss" module>
.ItemPanel {
  display: grid;
  gap: var(--space-5);
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
