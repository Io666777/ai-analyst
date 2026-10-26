<template>
  <div :class="$style.TopPanel">
    <VCard>
      <div :class="$style.settings">
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

        <fieldset :class="$style.period">
          <legend :class="$style.legend">Период</legend>
          <div :class="$style.periods" role="group" aria-label="Быстрый выбор периода">
            <VButton
              v-for="value in Object.values(TOP_PERIODS)"
              :key="value"
              :variant="period === value ? BUTTON_VARIANTS.primary : BUTTON_VARIANTS.secondary"
              :size="BUTTON_SIZES.small"
              :aria-pressed="period === value"
              @click="applyPeriod(value)"
            >
              {{ TOP_PERIOD_LABELS[value] }}
            </VButton>
          </div>
          <VDateRange
            :class="$style.range"
            :model-value="{ from: dateFrom, to: dateTo }"
            label="Свой период"
            placeholder="За всё время"
            :min="dataStart"
            :max="dataEnd"
            clearable
            clear-label="За всё время"
            @update:model-value="setRange"
          />
        </fieldset>
      </div>
    </VCard>

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
      <p :class="$style.summary">
        {{ formatDate(data.date_from) }} - {{ formatDate(data.date_to) }} · вся выручка периода:
        <strong>{{ formatMoney(data.total, data.currency) }}</strong>
      </p>
      <p v-if="!data.rows.length" :class="$style.note">За этот период продаж нет.</p>

      <template v-else>
        <VChart
          :option="chartOption"
          :description="`${title}: доли в выручке периода, кольцом`"
          :size="CHART_SIZES.large"
          :download-name="`топ-${data.by_label}`"
        />
        <p :class="$style.note">
          Кольцо - вся выручка периода.
          <template v-if="data.rows.length > CHART_MAX_ROWS">
            Своим цветом - первые {{ CHART_MAX_ROWS }}, остальные строки - в таблице.
          </template>
          Серый сектор - всё, что не вошло в список.
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
                <td :class="$style.name">
                  <!-- Цвет сектора на кольце: связывает строку таблицы с графиком -->
                  <span
                    v-if="index < CHART_MAX_ROWS"
                    :class="$style.dot"
                    :style="{ background: palette.categories[index % palette.categories.length] }"
                    aria-hidden="true"
                  />
                  <!-- Топ товаров: строка ведёт в карточку товара -->
                  <NuxtLink
                    v-if="data.by === ITEM_FIELD"
                    :to="{ path: ROUTES.item, query: { q: row.name } }"
                    :class="$style.link"
                  >
                    {{ row.name }}
                  </NuxtLink>
                  <template v-else>{{ row.name }}</template>
                </td>
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
 * Топ: лучшие или худшие товары, категории, бренды за период - кольцо долей и таблица.
 * Параметры меняются - топ пересчитывается сам, без кнопки.
 */
import { computed } from 'vue';
import { NuxtLink } from '#components';
import { useSession } from '~/entities/session';
import { ROUTES } from '~/shared/config';
import { capitalize, formatDate, formatMoney, formatPercent } from '~/shared/lib';
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
  VCheckbox,
  VDateRange,
  VSelect,
  VSpinner,
} from '~/shared/ui';
import { TOP_PERIOD_LABELS, TOP_PERIODS } from '../lib/periods';
import { CHART_MAX_ROWS, topChartOption } from '../lib/top-chart';
import { useTop } from '../model/useTop';

/** Поле «товар»: только у него есть карточка. */
const ITEM_FIELD = 'object';

const {
  field,
  size,
  worst,
  dateFrom,
  dateTo,
  period,
  data,
  isLoading,
  error,
  fieldOptions,
  sizeOptions,
  setRange,
  applyPeriod,
  reload,
} = useTop();

const session = useSession();
const dataStart = session.state.value.prepared?.date_from;
const dataEnd = session.state.value.prepared?.date_to;

// Цвета из CSS-токенов: одни и те же у секторов кольца и у точек в таблице
const palette = readChartPalette();

const title = computed(() => {
  if (!data.value) return '';
  return `${data.value.worst ? 'Худшие' : 'Лучшие'}: ${data.value.by_label}`;
});

const chartOption = computed(() =>
  data.value
    ? topChartOption(
        { rows: data.value.rows, total: data.value.total, currency: data.value.currency },
        palette,
      )
    : {},
);
</script>

<style lang="scss" module>
.TopPanel {
  display: grid;
  gap: var(--space-5);
}

.settings {
  display: grid;
  grid-template-columns: minmax(0, 1fr); // колонка - по ширине карточки, а не по содержимому
  gap: var(--space-4);
}

.controls {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
  gap: var(--space-4);
  align-items: end;
}

.period {
  display: grid;
  gap: var(--space-3);
  min-width: 0;
  padding: 0;
  margin: 0;
  border: 0;
}

.legend {
  padding: 0;
  margin-bottom: var(--space-2);
  color: var(--base-700);

  @include text(small);
}

.periods {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.range {
  max-width: 18rem;
}

.summary {
  margin-bottom: var(--space-3);
  color: var(--base-700);

  @include text(small);
}

.name {
  display: flex;
  gap: var(--space-2);
  align-items: center;
}

.dot {
  flex-shrink: 0;
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 50%;
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
    border-bottom: var(--border-width) solid var(--base-100);
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

.link {
  color: var(--primary-600);

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: var(--focus-width);
  }
}
</style>
