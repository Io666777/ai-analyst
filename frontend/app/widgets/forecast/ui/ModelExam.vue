<template>
  <div :class="$style.ModelExam">
    <p :class="$style.note">
      Каждая модель прогнозировала ваши прошлые продажи, будто будущего ещё не было, - и прогноз
      сравнили с тем, что случилось на самом деле. Выбрана та, что ошиблась меньше.
    </p>
    <div :class="$style.tableWrap">
      <table :class="$style.table">
        <caption :class="$style.caption">Проверка моделей на прошлых продажах</caption>
        <thead>
          <tr>
            <th scope="col">Модель</th>
            <th scope="col" :class="$style._number">Ошибка по дням</th>
            <th scope="col" :class="$style._number">Ошибка итога за период</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="score in models" :key="score.model" :class="{ [$style._chosen]: score.chosen }">
            <td>
              {{ score.model }}
              <span v-if="score.chosen" :class="$style.badge">выбрана</span>
            </td>
            <td :class="$style._number">{{ formatPercent(score.error_percent, false) }}</td>
            <td :class="$style._number">{{ formatPercent(score.total_error_percent) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p :class="$style.note">
      Ошибка по дням - насколько в среднем промахивается каждый день. Ошибка итога - насколько
      сумма за весь период больше (+) или меньше (−) правды: для плана закупок важна она.
    </p>
  </div>
</template>

<script setup lang="ts">
/**
 * Как выбрана модель: экзамен каждой модели на прошлых продажах того же горизонта.
 *
 * @example
 * <ModelExam :models="forecast.models" />
 */
import type { DeepReadonly } from 'vue';
import type { ModelScore } from '~/shared/api';
import { formatPercent } from '~/shared/lib';

defineProps<{
  /** Модели - выбранная первой. */
  models: DeepReadonly<ModelScore[]>;
}>();
</script>

<style lang="scss" module>
.ModelExam {
  display: grid;
  gap: var(--space-3);
}

.note {
  max-width: 45rem;
  color: var(--base-700);

  @include text(small);
}

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

._chosen {
  font-weight: 600;
}

.badge {
  display: inline-block;
  margin-left: var(--space-2);
  padding: 0 var(--space-2);
  color: var(--success-700);
  background: var(--success-100);
  border-radius: var(--radius-small);
  font-weight: 400;

  @include text(caption);
}

.caption {
  @include visually-hidden;
}
</style>
