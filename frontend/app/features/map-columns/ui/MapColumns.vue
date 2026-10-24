<template>
  <form :class="$style.MapColumns" novalidate @submit.prevent="handleSubmit">
    <p :class="$style.lead">
      Укажите, что значит каждая колонка. Обязательны дата и сумма (или цена и количество).
      Колонку с клиентами можно отметить - в анализ она не попадёт.
    </p>

    <VSpinner v-if="isLoadingOptions" label="Загружаю список ролей..." show-label />

    <div v-else :class="$style.columns">
      <VSelect
        v-for="column in columns"
        :key="column.name"
        v-model="mapping[column.name]"
        :label="column.name"
        :options="roleOptions"
        :hint="examplesHint(column.examples)"
        :error="errors.byColumn[column.name]"
      />
    </div>

    <VAlert
      v-if="errors.general.length"
      :variant="ALERT_VARIANTS.error"
      title="Разметку пока не принять"
    >
      <ul :class="$style.errorList">
        <li v-for="message in errors.general" :key="message">{{ message }}</li>
      </ul>
    </VAlert>
    <VAlert v-if="requestError" :variant="ALERT_VARIANTS.error">{{ requestError }}</VAlert>

    <div :class="$style.actions">
      <VButton type="submit" :loading="isSaving" :disabled="isLoadingOptions">
        Готово
      </VButton>
      <VButton
        v-if="cancelable"
        :variant="BUTTON_VARIANTS.ghost"
        :disabled="isSaving"
        @click="emit('cancel')"
      >
        Отмена
      </VButton>
    </div>
  </form>
</template>

<script setup lang="ts">
/**
 * Разметка колонок: у каждой колонки - список ролей и примеры значений.
 * Проверка до отправки (дата, сумма, одна роль - одной колонке), затем сервер чистит данные.
 */
import type { DeepReadonly } from 'vue';
import { computed } from 'vue';
import { useSession } from '~/entities/session';
import { ALERT_VARIANTS, BUTTON_VARIANTS, VAlert, VButton, VSelect, VSpinner } from '~/shared/ui';
import { useMapColumns } from '../model/useMapColumns';

withDefaults(
  defineProps<{
    /** Показать «Отмена» - когда разметку меняют, а не делают впервые. */
    cancelable?: boolean;
  }>(),
  { cancelable: false },
);

const emit = defineEmits<{
  /** Разметка принята, данные подготовлены. */
  done: [];
  /** Передумали менять разметку. */
  cancel: [];
}>();

const session = useSession();
const { mapping, roleOptions, errors, requestError, isLoadingOptions, isSaving, submit } =
  useMapColumns();

const columns = computed(() => session.state.value.columns);

/**
 * Подсказка под списком: примеры значений колонки.
 * @param {DeepReadonly<string[]>} examples - примеры.
 * @returns {string} "Примеры: 01.10.24, 02.10.24".
 */
function examplesHint(examples: DeepReadonly<string[]>): string {
  return examples.length ? `Примеры: ${examples.join(', ')}` : 'Колонка пустая';
}

/** «Готово». */
async function handleSubmit(): Promise<void> {
  if (await submit()) emit('done');
}
</script>

<style lang="scss" module>
.MapColumns {
  display: grid;
  gap: var(--space-4);
}

.lead {
  color: var(--base-700);

  @include text(small);
}

.columns {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: var(--space-4);
}

.errorList {
  display: grid;
  gap: var(--space-1);
  padding-left: var(--space-4);
  list-style: disc;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
