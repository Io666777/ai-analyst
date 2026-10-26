<template>
  <div :class="$style.SessionColumns">
    <table :class="$style.table">
      <caption :class="$style.caption">Колонки файла и примеры значений</caption>
      <thead>
        <tr>
          <th scope="col" :class="$style.head">Колонка</th>
          <th scope="col" :class="$style.head">Примеры значений</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="column in columns" :key="column.name" :class="$style.row">
          <th scope="row" :class="$style.name">{{ column.name }}</th>
          <td :class="$style.examples">
            {{ column.examples.length ? column.examples.join(', ') : EMPTY_VALUE }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
/**
 * Колонки открытого файла с примерами значений - по ним человек понимает, что в каждой колонке.
 *
 * @example
 * <SessionColumns :columns="session.state.value.columns" />
 */
import type { DeepReadonly } from 'vue';
import type { ColumnPreview } from '~/shared/api';
import { EMPTY_VALUE } from '~/shared/config';

defineProps<{
  /** Колонки из ответа на загрузку файла. */
  columns: DeepReadonly<ColumnPreview[]>;
}>();
</script>

<style lang="scss" module>
.SessionColumns {
  overflow-x: auto; // на телефоне длинная таблица прокручивается вбок, а не ломает страницу
}

.table {
  width: 100%;
  border-collapse: collapse;

  @include text(small);
}

.caption {
  @include visually-hidden;
}

.head {
  padding: var(--space-2) var(--space-3);
  color: var(--base-500);
  text-align: left;
  font-weight: 600;
  border-bottom: var(--border-width) solid var(--base-300);
}

.row:not(:last-child) {
  border-bottom: var(--border-width) solid var(--base-100);
}

.name {
  padding: var(--space-2) var(--space-3);
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
}

.examples {
  padding: var(--space-2) var(--space-3);
  color: var(--base-700);
}
</style>
