<template>
  <div :class="$style.PreparationReport">
    <dl :class="$style.numbers">
      <div :class="$style.item">
        <dt :class="$style.term">Было строк</dt>
        <dd :class="$style.value">{{ formatNumber(prepared.report.rows_before) }}</dd>
      </div>
      <div :class="$style.item">
        <dt :class="$style.term">Удалено «Итого» и пустых</dt>
        <dd :class="$style.value">{{ formatNumber(prepared.report.removed_totals_and_empty) }}</dd>
      </div>
      <div :class="$style.item">
        <dt :class="$style.term">Удалено без даты</dt>
        <dd :class="$style.value">{{ formatNumber(prepared.report.removed_without_date) }}</dd>
      </div>
      <div :class="$style.item">
        <dt :class="$style.term">Осталось для анализа</dt>
        <dd :class="[$style.value, $style._accent]">{{ formatNumber(prepared.report.rows_after) }}</dd>
      </div>
    </dl>

    <p :class="$style.line">
      Период: {{ formatDate(prepared.date_from) }} - {{ formatDate(prepared.date_to) }}
    </p>
    <p :class="$style.line">Нашлись поля: {{ fieldNames }}</p>
  </div>
</template>

<script setup lang="ts">
/**
 * Что программа сделала с данными после разметки: сколько строк было, что удалено и почему,
 * за какой период данные и какие поля нашлись. Ничего не теряется молча.
 *
 * @example
 * <PreparationReport :prepared="session.state.value.prepared" :field-labels="labels" />
 */
import type { DeepReadonly } from 'vue';
import { computed } from 'vue';
import type { PreparedData } from '~/shared/api';
import { formatDate, formatNumber } from '~/shared/lib';

const props = defineProps<{
  /** Ответ сервера на разметку. */
  prepared: DeepReadonly<PreparedData>;
  /** Подписи основных полей: date → "дата". Дополнительные поля - под своими названиями. */
  fieldLabels: Readonly<Record<string, string>>;
}>();

const fieldNames = computed(() =>
  props.prepared.fields.map(field => props.fieldLabels[field] ?? field).join(', '),
);
</script>

<style lang="scss" module>
.PreparationReport {
  display: grid;
  gap: var(--space-3);
}

.numbers {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: var(--space-4);
  margin: 0;
}

.item {
  display: grid;
  gap: var(--space-1);
}

.term {
  color: var(--base-700);

  @include text(small);
}

.value {
  margin: 0;
  font-variant-numeric: tabular-nums;

  @include text(h2);

  &._accent {
    color: var(--success-700);
  }
}

.line {
  color: var(--base-700);

  @include text(small);
}
</style>
