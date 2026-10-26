<template>
  <label
    :class="classList"
    @dragenter.prevent="handleDragEnter"
    @dragover.prevent
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <input
      :class="$style.input"
      type="file"
      :accept="accept"
      :disabled="isDisabled"
      :aria-describedby="hint ? hintId : undefined"
      @change="handleChange"
    >

    <VSpinner v-if="loading" :label="loadingLabel" show-label />
    <template v-else>
      <span :class="$style.title">{{ label }}</span>
      <span v-if="hint" :id="hintId" :class="$style.hint">{{ hint }}</span>
    </template>
  </label>
</template>

<script setup lang="ts">
/**
 * Поле выбора файла: клик или перетаскивание файла мышью. Работает с клавиатуры
 * (Tab, затем Enter или пробел) - внутри настоящий input type="file".
 * Сам файл не проверяет и никуда не отправляет - только отдаёт наружу (select).
 *
 * @example
 * <VFileDrop accept=".csv,.xlsx" label="Перетащите файл сюда" @select="handleFile" />
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, ref, useCssModule, useId } from 'vue';
import { VSpinner } from '../VSpinner';

const props = withDefaults(
  defineProps<{
    /** Какие файлы предлагать в окне выбора: ".csv,.xlsx". */
    accept?: string;
    /** Главная надпись. */
    label?: string;
    /** Пояснение мелким шрифтом: форматы, размер. */
    hint?: string;
    /** Поле неактивно. */
    disabled?: boolean;
    /** Файл отправляется - вместо надписи спиннер. */
    loading?: boolean;
    /** Что показывать во время загрузки. */
    loadingLabel?: string;
  }>(),
  {
    accept: undefined,
    label: 'Перетащите файл сюда или нажмите, чтобы выбрать',
    hint: undefined,
    disabled: false,
    loading: false,
    loadingLabel: 'Загружаю файл...',
  },
);

const emit = defineEmits<{
  /** Выбран файл. */
  select: [file: File];
}>();

const style = useCssModule();
const hintId = useId();

// Счётчик, а не флаг: dragenter/dragleave срабатывают и на вложенных элементах -
// иначе подсветка мигала бы, пока файл тащат над надписью
const dragDepth = ref(0);

const isDisabled = computed(() => props.disabled || props.loading);

const classList = computed(() => [
  style.VFileDrop,
  {
    [style._dragging]: dragDepth.value > 0,
    [style._disabled]: isDisabled.value,
  },
]);

/**
 * Отдаёт файл наружу, если поле активно.
 * @param {File | undefined} file - выбранный файл.
 */
function emitFile(file: File | undefined): void {
  if (!file || isDisabled.value) return;
  emit('select', file);
}

/**
 * Файл выбран в окне выбора.
 * @param {Event} event - событие выбора.
 */
function handleChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  emitFile(input.files?.[0]);
  input.value = ''; // тот же файл можно выбрать ещё раз - например, после исправления
}

/** Файл занесли над полем. */
function handleDragEnter(): void {
  dragDepth.value += 1;
}

/** Файл увели с поля. */
function handleDragLeave(): void {
  dragDepth.value = Math.max(0, dragDepth.value - 1);
}

/**
 * Файл бросили на поле.
 * @param {DragEvent} event - событие перетаскивания.
 */
function handleDrop(event: DragEvent): void {
  dragDepth.value = 0;
  emitFile(event.dataTransfer?.files[0]);
}
</script>

<style lang="scss" module>
.VFileDrop {
  display: grid;
  gap: var(--space-2);
  place-items: center;
  min-height: 10rem;
  padding: var(--space-6) var(--space-5);
  color: var(--primary-600);
  text-align: center;
  cursor: pointer;
  user-select: none;
  background: var(--white);
  border: var(--focus-width) dashed var(--primary-300);
  border-radius: var(--radius-large);
  transition:
    background var(--default-transition),
    border-color var(--default-transition);

  &:hover,
  &._dragging {
    background: var(--primary-100);
    border-color: var(--primary-500);
  }

  // Фокус с клавиатуры - на невидимом input, рамку рисуем у всего поля
  &:focus-within {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: var(--focus-width);
  }

  &._disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }
}

.input {
  @include visually-hidden;
}

.title {
  @include text(body);

  font-weight: 600;
}

.hint {
  color: var(--base-500);

  @include text(small);
}
</style>
