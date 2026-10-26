<template>
  <div :class="$style.ForecastPanel">
    <VCard v-if="!data || isLoading">
      <div :class="$style.start">
        <p :class="$style.lead">
          Программа сама проверит несколько моделей на ваших прошлых продажах, выберет самую
          точную и подскажет, на сколько дней вперёд прогнозу можно верить.
        </p>
        <div :class="$style.action">
          <VButton :loading="isLoading" @click="calculate">Посчитать прогноз</VButton>
          <!-- Диктор прочитает, что расчёт идёт; секунды - только для глаз, чтобы не мешать -->
          <p v-if="isLoading" :class="$style.note" role="status">
            Считаю, это до минуты<span aria-hidden="true">: {{ elapsed }} с</span>
          </p>
        </div>
      </div>
    </VCard>

    <VAlert v-if="error" :variant="ALERT_VARIANTS.error" title="Прогноз не посчитался">
      {{ error }}
    </VAlert>

    <template v-if="data && !isLoading">
      <!-- Мало данных: прогноза нет, только объяснение -->
      <VAlert v-if="data.step === STEPS.none" :variant="ALERT_VARIANTS.info" title="Прогноз пока не сделать">
        {{ data.message }}
      </VAlert>

      <!-- Данных немного: простые средние вместо прогноза -->
      <VCard v-else-if="data.step === STEPS.estimate && data.estimate" title="Пока - оценка, а не прогноз">
        <p :class="$style.lead">{{ data.message }}</p>
        <div :class="[$style.metrics, $style._spaced]">
          <VMetric
            label="В среднем в день"
            :value="data.estimate.per_day"
            :currency="data.currency"
            hint="За последние 2 недели"
          />
          <VMetric
            label="Если так пойдёт дальше"
            :value="data.estimate.projection"
            :currency="data.currency"
            hint="За следующие 30 дней"
          />
        </div>
        <p :class="[$style.note, $style._spaced]">В среднем по дням недели</p>
        <!-- Плитки, а не таблица: на телефоне сами переносятся на вторую строку -->
        <dl :class="$style.weekdays">
          <div v-for="(value, day) in data.estimate.by_weekday" :key="day" :class="$style.weekday">
            <dt :class="$style.day">{{ day }}</dt>
            <dd :class="$style.amount">{{ formatMoney(value, data.currency) }}</dd>
          </div>
        </dl>
      </VCard>

      <!-- Прогноз с проверенной точностью -->
      <template v-else-if="data.step === STEPS.forecast">
        <!-- message здесь не показываем: его цифры - в карточках ниже, вывод - в accuracy.summary -->
        <VCard :title="`Прогноз на ${pluralize(data.horizon_days ?? 0, DAY_FORMS)}`">
          <div :class="$style.metrics">
            <VMetric
              v-if="data.total !== null && data.total !== undefined"
              label="Ожидаемая выручка"
              :value="data.total"
              :currency="data.currency"
              :change="data.year_ago ? data.year_ago.change_percent : undefined"
              :change-label="data.year_ago ? 'к тем же дням год назад' : undefined"
              :hint="corridorHint"
            />
            <!-- Год назад: те же дни недели, 52 недели назад - честное сравнение с сезоном -->
            <VMetric
              v-if="data.year_ago"
              label="Год назад за те же дни"
              :value="data.year_ago.value"
              :currency="data.currency"
              :hint="`${formatDate(data.year_ago.date_from)} - ${formatDate(data.year_ago.date_to)}`"
            />
            <div v-if="data.accuracy" :class="$style.accuracy">
              <p :class="$style.note">Точность</p>
              <p :class="$style.level">{{ capitalize(data.accuracy.level) }}</p>
              <p :class="$style.note">
                Ошибка по дням - около {{ formatPercent(data.accuracy.error_percent, false) }}
              </p>
            </div>
          </div>

          <div v-if="data.accuracy" :class="$style.why">
            <p>{{ data.accuracy.summary }}</p>
            <ul v-if="data.accuracy.reasons.length" :class="$style.reasons">
              <li v-for="reason in data.accuracy.reasons" :key="reason">{{ reason }}</li>
            </ul>
          </div>
          <p v-if="data.model" :class="$style.note">
            Модель: {{ data.model }} - выбрана как самая точная на ваших прошлых продажах.
          </p>
        </VCard>

        <VCard title="Продажи по дням: факт и прогноз">
          <VChart
            :option="chartOption"
            :description="chartDescription"
            :size="CHART_SIZES.large"
            zoomable
            download-name="прогноз"
          />
          <p :class="$style.note">
            Пунктир - прогноз, полоса - коридор: в 8 случаях из 10 реальные продажи окажутся внутри.
            Клик по названию в легенде прячет линию.
          </p>
        </VCard>

        <VCard v-if="data.weeks.length" title="Сколько ждать">
          <ForecastPeriods :weeks="data.weeks" :months="data.months" :currency="data.currency" />
        </VCard>

        <VCard v-if="data.models.length > 1" title="Как выбрана модель">
          <ModelExam :models="data.models" />
        </VCard>
      </template>

      <div>
        <VButton :variant="BUTTON_VARIANTS.ghost" :size="BUTTON_SIZES.small" @click="calculate">
          Посчитать заново
        </VButton>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Прогноз продаж по кнопке: долгий расчёт на сервере (до минуты), затем одно из трёх -
 * «мало данных», «оценка простыми средними» или прогноз с точностью и графиком.
 */
import { computed } from 'vue';
import { capitalize, formatDate, formatMoney, formatPercent, pluralize, type WordForms } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_SIZES,
  BUTTON_VARIANTS,
  CHART_SIZES,
  readChartColors,
  VAlert,
  VButton,
  VCard,
  VChart,
  VMetric,
} from '~/shared/ui';
import { forecastChartOption } from '../lib/forecast-chart';
import { useForecast } from '../model/useForecast';
import ForecastPeriods from './ForecastPeriods.vue';
import ModelExam from './ModelExam.vue';

/** Ступеньки холодного старта - как в ответе сервера (step). */
const STEPS = { none: 'none', estimate: 'estimate', forecast: 'forecast' } as const;
const DAY_FORMS: WordForms = { one: 'день', few: 'дня', many: 'дней' };

const { data, isLoading, error, elapsed, calculate } = useForecast();

const corridorHint = computed(() => {
  const corridor = data.value?.corridor;
  if (!corridor || !data.value) return undefined;
  const [low, high] = corridor;
  return `Скорее всего от ${formatMoney(low, data.value.currency)} до ${formatMoney(high, data.value.currency)}`;
});

const chartOption = computed(() =>
  data.value
    ? forecastChartOption(
        { history: data.value.history, points: data.value.points, currency: data.value.currency },
        readChartColors(),
      )
    : {},
);

const chartDescription = computed(() => {
  const points = data.value?.points ?? [];
  const first = points[0];
  const last = points.at(-1);
  if (!first || !last) return 'Продажи по дням';
  return `Продажи по дням: факт и прогноз с ${formatDate(first.period)} по ${formatDate(last.period)}`;
});
</script>

<style lang="scss" module>
.ForecastPanel {
  display: grid;
  gap: var(--space-5);
}

.start {
  display: grid;
  gap: var(--space-4);
}

.lead {
  max-width: 45rem;
  color: var(--base-700);
}

.action {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
}

.note {
  color: var(--base-700);

  @include text(small);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: var(--space-5);
}

._spaced {
  margin-top: var(--space-4);
}

.accuracy {
  display: grid;
  gap: var(--space-1);
  align-content: start;
}

.level {
  color: var(--base-900);

  @include text(metric);

  @include respond-to(mobile) {
    @include text(h1);
  }
}

.why {
  display: grid;
  gap: var(--space-2);
  margin-top: var(--space-4);
  color: var(--base-900);
}

.reasons {
  display: grid;
  gap: var(--space-1);
  padding-left: var(--space-4);
  color: var(--base-700);
  list-style: disc;

  @include text(small);
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(5.5rem, 1fr));
  gap: var(--space-2);
  margin: var(--space-2) 0 0;
}

.weekday {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-2);
  text-align: center;
  background: var(--base-50);
  border-radius: var(--radius-small);
}

.day {
  color: var(--base-700);

  @include text(small);
}

.amount {
  margin: 0;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;

  @include text(small);

  font-weight: 600;
}
</style>
