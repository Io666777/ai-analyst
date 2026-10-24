<template>
  <div :class="$style.OverviewPanel">
    <VSpinner v-if="isLoading && !data" label="Считаю обзор..." show-label />

    <div v-else-if="error" :class="$style.error">
      <VAlert :variant="ALERT_VARIANTS.error" title="Обзор не посчитался">{{ error }}</VAlert>
      <div>
        <VButton :variant="BUTTON_VARIANTS.secondary" @click="run()">Попробовать ещё раз</VButton>
      </div>
    </div>

    <template v-else-if="data">
      <p :class="$style.period">
        Данные: {{ formatDate(data.date_from) }} - {{ formatDate(data.date_to) }}
      </p>

      <VCard :title="data.last_month ? `Как прошёл ${data.last_month.month}` : 'Итоги'">
        <div :class="$style.metrics">
          <template v-if="data.last_month">
            <VMetric
              :label="`Выручка: ${data.last_month.month}`"
              :value="data.last_month.after"
              :currency="data.currency"
              :change="data.last_month.change_percent"
              change-label="к прошлому месяцу"
              :hint="`${capitalize(data.last_month.previous_month)}: ${formatMoney(data.last_month.before, data.currency)}`"
            />
            <VMetric
              label="В среднем за день"
              :value="data.last_month.per_day_after"
              :currency="data.currency"
              :change="data.last_month.per_day_change_percent"
              change-label="к прошлому месяцу"
              hint="Честнее, когда в месяцах разное число дней"
            />
          </template>
          <VMetric
            label="Выручка за весь период"
            :value="data.total"
            :currency="data.currency"
            hint="Без строк, исключённых в настройках"
          />
        </div>
        <VAlert v-if="data.last_month_note" :variant="ALERT_VARIANTS.info">
          {{ data.last_month_note }}
        </VAlert>
      </VCard>

      <VCard title="Выручка по месяцам">
        <RevenueChart
          v-if="data.monthly.length"
          :points="data.monthly"
          :currency="data.currency"
        />
        <p v-else :class="$style.note">Нет ни одного полного месяца - графику не из чего строиться.</p>
        <p v-if="data.incomplete.length" :class="$style.note">
          Не показаны неполные месяцы - иначе они выглядели бы как обвал продаж:
          {{ data.incomplete.join(', ') }}.
        </p>
      </VCard>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Обзор продаж: последний полный месяц против предыдущего, итог за всё время
 * и выручка по месяцам. Загружается сам при появлении на экране.
 */
import { onMounted } from 'vue';
import { RevenueChart } from '~/entities/revenue';
import { toApiError } from '~/shared/api';
import { capitalize, formatDate, formatMoney, useRequest } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_VARIANTS,
  VAlert,
  VButton,
  VCard,
  VMetric,
  VSpinner,
} from '~/shared/ui';
import { fetchOverview } from '../api/overview-api';

const { data, isLoading, error, run } = useRequest(fetchOverview, err => toApiError(err).message);

onMounted(run);
</script>

<style lang="scss" module>
.OverviewPanel {
  display: grid;
  gap: var(--space-5);
}

.error {
  display: grid;
  gap: var(--space-3);
}

.period {
  color: var(--base-700);

  @include text(small);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: var(--space-5);
}

.note {
  color: var(--base-700);

  @include text(small);
}
</style>
