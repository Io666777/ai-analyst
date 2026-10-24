<template>
  <div :class="$style.ComparePanel">
    <VCard>
      <form :class="$style.form" novalidate @submit.prevent="submit">
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
          <fieldset v-for="period in PERIODS" :key="period.key" :class="$style.period">
            <legend :class="$style.legend">{{ period.label }}</legend>
            <div :class="$style.dates">
              <VInput
                :model-value="pair[period.key].from"
                :type="INPUT_TYPES.date"
                label="С"
                :error="errors[`${period.key}.from`]"
                @update:model-value="setDate(period.key, 'from', $event)"
              />
              <VInput
                :model-value="pair[period.key].to"
                :type="INPUT_TYPES.date"
                label="По, включительно"
                :error="errors[`${period.key}.to`]"
                @update:model-value="setDate(period.key, 'to', $event)"
              />
            </div>
          </fieldset>
        </div>

        <div>
          <VButton type="submit" :loading="isLoading">Сравнить</VButton>
        </div>
      </form>
    </VCard>

    <VAlert v-if="error" :variant="ALERT_VARIANTS.error" title="Сравнение не посчиталось">
      {{ error }}
    </VAlert>

    <VCard v-else-if="data" title="Было и стало" :aria-busy="isLoading">
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
  </div>
</template>

<script setup lang="ts">
/**
 * Сравнение двух периодов: готовые варианты (месяц к месяцу, год к году, 30 дней)
 * или свои даты. Итоги, изменение, среднее за день и предупреждения сервера.
 */
import type { DeepReadonly } from 'vue';
import type { PeriodTotal } from '~/shared/api';
import { formatDate, formatMoney, pluralize, type WordForms } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_SIZES,
  BUTTON_VARIANTS,
  INPUT_TYPES,
  VAlert,
  VButton,
  VCard,
  VInput,
  VMetric,
} from '~/shared/ui';
import { PRESET_LABELS, PRESETS } from '../lib/presets';
import { useCompare } from '../model/useCompare';

const DAY_FORMS: WordForms = { one: 'день', few: 'дня', many: 'дней' };

const PERIODS = [
  { key: 'first', label: 'Было' },
  { key: 'second', label: 'Стало' },
] as const;

const { pair, preset, errors, data, isLoading, error, setDate, applyPreset, submit } =
  useCompare();

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
  grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
  gap: var(--space-4);

  @include respond-to(mobile) {
    grid-template-columns: 1fr;
  }
}

.period {
  display: grid;
  gap: var(--space-2);
  min-width: 0;
  padding: var(--space-3) var(--space-4) var(--space-4);
  margin: 0;
  border: var(--border-width) solid var(--base-100);
  border-radius: var(--radius);
}

.legend {
  padding: 0 var(--space-1);

  @include text(h3);
}

.dates {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  align-content: start;

  @include respond-to(mobile) {
    grid-template-columns: 1fr;
  }
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

.warnings {
  display: grid;
  gap: var(--space-1);
  padding-left: var(--space-4);
  list-style: disc;
}
</style>
