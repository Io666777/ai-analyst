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
        <template v-if="data.monthly.length">
          <p :class="$style.note">Нажмите на месяц - покажу, какие товары дали выручку и как шли дни.</p>
          <RevenueChart
            :points="data.monthly"
            :currency="data.currency"
            selectable
            :selected="month"
            @select="openMonth"
          />
          <!-- То же без мыши: по холсту графика не пройти клавиатурой, по списку - можно -->
          <VSelect
            v-model="monthModel"
            :class="$style.monthSelect"
            label="Подробнее о месяце"
            placeholder="Выберите месяц"
            :options="monthOptions"
          />
        </template>
        <p v-else :class="$style.note">Нет ни одного полного месяца - графику не из чего строиться.</p>
        <p v-if="data.incomplete.length" :class="$style.note">
          Не показаны неполные месяцы - иначе они выглядели бы как обвал продаж:
          {{ data.incomplete.join(', ') }}.
        </p>
      </VCard>

      <section v-if="month" ref="details" :class="$style.details">
        <VCard :title="capitalize(formatMonth(month))">
          <template #actions>
            <VButton :variant="BUTTON_VARIANTS.ghost" :size="BUTTON_SIZES.small" @click="month = null">
              Скрыть
            </VButton>
          </template>
          <MonthDetails :month="month" />
        </VCard>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Обзор продаж: последний полный месяц против предыдущего, итог за всё время
 * и выручка по месяцам. Загружается сам при появлении на экране.
 */
import { computed, nextTick, onMounted, useTemplateRef } from 'vue';
import { RevenueChart } from '~/entities/revenue';
import { useSessionState } from '~/entities/session';
import { toApiError } from '~/shared/api';
import { capitalize, formatDate, formatMoney, formatMonth, useRequest } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_SIZES,
  BUTTON_VARIANTS,
  type SelectOption,
  VAlert,
  VButton,
  VCard,
  VMetric,
  VSelect,
  VSpinner,
} from '~/shared/ui';
import { fetchOverview } from '../api/overview-api';
import MonthDetails from './MonthDetails.vue';

const { data, isLoading, error, run } = useRequest(fetchOverview, err => toApiError(err).message);

// Открытый месяц "2026-09" переживает переключение вкладок
const month = useSessionState<string | null>('overview-month', () => null);
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
 * Открыть подробности месяца и прокрутить к ним - иначе под графиком их можно не заметить.
 * @param {string} period - месяц "2026-09".
 */
async function openMonth(period: string): Promise<void> {
  month.value = period || null;
  await nextTick();
  details.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

onMounted(run);
</script>

<style lang="scss" module>
.OverviewPanel {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-5);
}

.monthSelect {
  max-width: 18rem;
  margin-top: var(--space-3);
}

// Прокрутка к подробностям - с отступом, чтобы карточку не закрыла шапка
.details {
  scroll-margin-top: var(--space-4);
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
