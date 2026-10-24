<template>
  <div :class="$style.TopPanel">
    <div :class="$style.controls">
      <VSelect
        v-model="field"
        label="Что сравнивать"
        :options="fieldOptions"
        :disabled="!fieldOptions.length"
      />
      <VSelect v-model="size" label="Сколько строк" :options="sizeOptions" />
      <VCheckbox v-model="worst" :class="$style.worst" label="Худшие вместо лучших" />
    </div>

    <VSpinner v-if="isLoading && !data" label="Считаю топ..." show-label />

    <div v-else-if="error" :class="$style.error">
      <VAlert :variant="ALERT_VARIANTS.error" title="Топ не посчитался">{{ error }}</VAlert>
      <div>
        <VButton :variant="BUTTON_VARIANTS.secondary" @click="reload()">
          Попробовать ещё раз
        </VButton>
      </div>
    </div>

    <VCard v-else-if="data" :title="title" :aria-busy="isLoading">
      <p v-if="!data.rows.length" :class="$style.note">Нечего показать - продаж нет.</p>

      <template v-else>
        <VChart
          :option="chartOption"
          :description="`${title}: столбцы - выручка, подписи - доля от всей выручки`"
          :size="data.rows.length > CHART_SIZE_STEP ? CHART_SIZES.large : CHART_SIZES.medium"
          :download-name="`топ-${data.by_label}`"
        />
        <p v-if="data.rows.length > CHART_MAX_ROWS" :class="$style.note">
          На графике - первые {{ CHART_MAX_ROWS }}, все строки - в таблице.
        </p>

        <div :class="$style.tableWrap">
          <table :class="$style.table">
            <caption :class="$style.caption">{{ title }}</caption>
            <thead>
              <tr>
                <th scope="col" :class="$style._number">№</th>
                <th scope="col">{{ capitalize(data.by_label) }}</th>
                <th scope="col" :class="$style._number">Выручка</th>
                <th scope="col" :class="$style._number">Доля</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in data.rows" :key="row.name">
                <td :class="$style._number">{{ index + 1 }}</td>
                <td>{{ row.name }}</td>
                <td :class="$style._number">{{ formatMoney(row.value, data.currency) }}</td>
                <td :class="$style._number">{{ formatPercent(row.share_percent, false) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p :class="$style.note">Доля - от всей выручки за период, а не только от этого списка.</p>
      </template>
    </VCard>
  </div>
</template>

<script setup lang="ts">
/**
 * Топ: лучшие или худшие товары, категории, бренды - график и таблица.
 * Параметры меняются - топ пересчитывается сам, без кнопки.
 */
import { computed } from 'vue';
import { capitalize, formatMoney, formatPercent } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_VARIANTS,
  CHART_SIZES,
  VAlert,
  VButton,
  VCard,
  VChart,
  VCheckbox,
  VSelect,
  VSpinner,
} from '~/shared/ui';
import { CHART_MAX_ROWS, topChartOption } from '../lib/top-chart';
import { useTop } from '../model/useTop';

/** Больше строк - график выше, чтобы столбцы не сжимались в нитки. */
const CHART_SIZE_STEP = 10;

const { field, size, worst, data, isLoading, error, fieldOptions, sizeOptions, reload } = useTop();

const title = computed(() => {
  if (!data.value) return '';
  return `${data.value.worst ? 'Худшие' : 'Лучшие'}: ${data.value.by_label}`;
});

const chartOption = computed(() =>
  data.value ? topChartOption(data.value.rows, data.value.currency) : {},
);
</script>

<style lang="scss" module>
.TopPanel {
  display: grid;
  gap: var(--space-5);
}

.controls {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
  gap: var(--space-4);
  align-items: end;
}

// Флажок - на одной линии с полями выбора, а не с их подписями
.worst {
  align-items: center;
  min-height: var(--control-height);
}

.error {
  display: grid;
  gap: var(--space-3);
}

.note {
  color: var(--base-700);

  @include text(small);
}

// Таблица шире экрана телефона - прокручивается сама, а не вся страница
.tableWrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;

  @include text(small);

  th,
  td {
    padding: var(--space-2) var(--space-3);
    text-align: left;
    border-bottom: 1px solid var(--base-100);
  }

  th {
    color: var(--base-700);
    font-weight: 600;
  }

  ._number {
    text-align: right;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }
}

.caption {
  @include visually-hidden;
}
</style>
