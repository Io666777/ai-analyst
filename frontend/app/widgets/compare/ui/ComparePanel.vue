<template>
  <div :class="$style.ComparePanel">
    <VCard>
      <div :class="$style.form">
        <div :class="$style.presets" role="group" aria-label="Готовые варианты">
          <VButton
            v-for="value in Object.values(PRESETS)"
            :key="value"
            :variant="preset === value ? BUTTON_VARIANTS.primary : BUTTON_VARIANTS.secondary"
            :size="BUTTON_SIZES.small"
            :aria-pressed="preset === value"
            @click="applyPreset(value)"
          >
            {{ PRESET_LABELS[value] }}
          </VButton>
        </div>

        <div :class="$style.periods">
          <VDateRange
            v-for="period in PERIODS"
            :key="period.key"
            :model-value="pair[period.key]"
            :label="period.label"
            :min="dataStart"
            :max="dataEnd"
            @update:model-value="setPeriod(period.key, $event)"
          />
        </div>
      </div>
    </VCard>

    <VAlert v-if="error" :variant="ALERT_VARIANTS.error" title="Сравнение не посчиталось">
      {{ error }}
    </VAlert>

    <VSpinner v-else-if="isLoading && !data" label="Сравниваю..." show-label />

    <template v-else-if="data">
      <VCard title="Было и стало" :aria-busy="isLoading">
        <div :class="$style.metrics">
          <VMetric
            label="Было"
            :value="data.first.value"
            :currency="data.currency"
            :hint="periodHint(data.first)"
          />
          <VMetric
            label="Стало"
            :value="data.second.value"
            :currency="data.currency"
            :change="data.change_percent"
            change-label="к периоду «было»"
            :hint="periodHint(data.second)"
          />
          <VMetric
            label="Стало в среднем за день"
            :value="data.second.per_day"
            :currency="data.currency"
            :change="data.per_day_change_percent"
            change-label="к «было»"
            :hint="`Было: ${formatMoney(data.first.per_day, data.currency)} в день - честнее, если в периодах разное число дней`"
          />
        </div>
        <p :class="$style.difference">
          Разница: <strong>{{ signedMoney(data.change, data.currency) }}</strong>
        </p>

        <VAlert
          v-if="data.warnings.length"
          :variant="ALERT_VARIANTS.warning"
          title="Сравнение может быть нечестным"
        >
          <ul :class="$style.warnings">
            <li v-for="warning in data.warnings" :key="warning">{{ warning }}</li>
          </ul>
        </VAlert>
      </VCard>

      <VCard v-if="data.rows.length" :title="`${capitalize(data.by_label ?? '')}: было и стало`">
        <p v-if="leaders" :class="$style.leaders">
          <template v-if="leaders.grew">
            Сильнее всего вырос: <strong>{{ leaders.grew.name }}</strong>
            ({{ signedMoney(leaders.grew.change, data.currency) }}).
          </template>
          <template v-if="leaders.fell">
            Сильнее всего просел: <strong>{{ leaders.fell.name }}</strong>
            ({{ signedMoney(leaders.fell.change, data.currency) }})
          </template>
        </p>
        <VChart
          :option="chartOption"
          :description="`Выручка товаров: было и стало, ${data.rows.length} самых заметных`"
          :size="CHART_SIZES.large"
          download-name="сравнение-товаров"
        />
        <p :class="$style.note">
          Серый - было, синий - стало. Показаны {{ data.rows.length }} самых заметных: с
          наибольшей выручкой хотя бы в одном из периодов.
        </p>
      </VCard>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Сравнение двух периодов: готовые варианты (месяц к месяцу, год к году, 30 дней)
 * или свои периоды в календаре. Итоги, среднее за день, предупреждения
 * и товары парами столбцов «было / стало».
 */
import type { DeepReadonly } from 'vue';
import { computed } from 'vue';
import { useSession } from '~/entities/session';
import type { PeriodTotal } from '~/shared/api';
import { capitalize, formatDate, formatMoney, pluralize, type WordForms } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_SIZES,
  BUTTON_VARIANTS,
  CHART_SIZES,
  readChartPalette,
  VAlert,
  VButton,
  VCard,
  VChart,
  VDateRange,
  VMetric,
  VSpinner,
} from '~/shared/ui';
import { compareChartOption } from '../lib/compare-chart';
import { PRESET_LABELS, PRESETS } from '../lib/presets';
import { useCompare } from '../model/useCompare';

const DAY_FORMS: WordForms = { one: 'день', few: 'дня', many: 'дней' };

const PERIODS = [
  { key: 'first', label: 'Было' },
  { key: 'second', label: 'Стало' },
] as const;

const session = useSession();
const dataStart = session.state.value.prepared?.date_from;
const dataEnd = session.state.value.prepared?.date_to;

const { pair, preset, data, isLoading, error, setPeriod, applyPreset } = useCompare();

const palette = readChartPalette();

const chartOption = computed(() =>
  data.value ? compareChartOption(data.value.rows, data.value.currency, palette) : {},
);

// Кто сильнее всего вырос и просел - словами, над графиком
const leaders = computed(() => {
  const rows = data.value?.rows ?? [];
  if (!rows.length) return null;
  const sorted = [...rows].sort((a, b) => b.change - a.change);
  const grew = sorted[0].change > 0 ? sorted[0] : null;
  const fell = sorted.at(-1)!.change < 0 ? sorted.at(-1)! : null;
  return grew || fell ? { grew, fell } : null;
});

/**
 * Подпись периода: «01.08.2026 - 31.08.2026, 31 день».
 * @param {DeepReadonly<PeriodTotal>} period - период из ответа сервера.
 * @returns {string} подпись.
 */
function periodHint(period: DeepReadonly<PeriodTotal>): string {
  const dates = `${formatDate(period.date_from)} - ${formatDate(period.date_to)}`;
  return `${dates}, ${pluralize(period.days, DAY_FORMS)}`;
}

/**
 * Деньги со знаком: +1 535 р. или −1 535 р.
 * @param {number} value - сумма.
 * @param {string} currency - валюта.
 * @returns {string} сумма со знаком.
 */
function signedMoney(value: number, currency: string): string {
  if (!value) return formatMoney(0, currency);
  return `${value > 0 ? '+' : '−'}${formatMoney(Math.abs(value), currency)}`;
}
</script>

<style lang="scss" module>
.ComparePanel {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-5);
}

.form {
  display: grid;
  gap: var(--space-4);
}

.presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.periods {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(14rem, 18rem));
  gap: var(--space-4);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: var(--space-5);
}

.difference {
  color: var(--base-700);

  @include text(body);
}

.leaders {
  margin-bottom: var(--space-2);
  color: var(--base-900);

  @include text(small);
}

.note {
  color: var(--base-700);

  @include text(small);
}

.warnings {
  display: grid;
  gap: var(--space-1);
  padding-left: var(--space-4);
  list-style: disc;
}
</style>
