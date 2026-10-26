<template>
  <div :class="$style.VTabs">
    <div :class="$style.list" role="tablist" :aria-label="label">
      <button
        v-for="(tab, index) in tabs"
        :id="tabId(tab.value)"
        :key="tab.value"
        ref="buttons"
        type="button"
        role="tab"
        :class="[$style.tab, { [$style._active]: tab.value === modelValue }]"
        :aria-selected="tab.value === modelValue"
        :aria-controls="panelId"
        :tabindex="tab.value === modelValue ? 0 : -1"
        @click="select(tab.value)"
        @keydown="handleKeydown($event, index)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div :id="panelId" role="tabpanel" :aria-labelledby="tabId(modelValue)" tabindex="0">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Вкладки: одна панель, содержимое - в слоте по выбранной вкладке.
 * Клавиатура как у обычных вкладок: Tab - на выбранную вкладку, стрелки - соседняя,
 * Home / End - первая / последняя.
 *
 * @example
 * <VTabs v-model="view" label="Подробности месяца" :tabs="[{ value: 'items', label: 'Товары' }]">
 *   <ItemsTable v-if="view === 'items'" />
 * </VTabs>
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { nextTick, useId, useTemplateRef } from 'vue';
import type { TabOption } from './types';

const props = defineProps<{
  /** Выбранная вкладка (v-model). */
  modelValue: string;
  /** Вкладки. */
  tabs: TabOption[];
  /** Что за вкладки - для экранного диктора. */
  label: string;
}>();

const emit = defineEmits<{
  /** Выбрана вкладка. */
  'update:modelValue': [value: string];
}>();

const KEYS = { left: 'ArrowLeft', right: 'ArrowRight', home: 'Home', end: 'End' } as const;

const baseId = useId();
const panelId = `${baseId}-panel`;
const buttons = useTemplateRef<HTMLButtonElement[]>('buttons');

/**
 * id кнопки вкладки - панель ссылается на него в aria-labelledby.
 * @param {string} value - значение вкладки.
 * @returns {string} id.
 */
function tabId(value: string): string {
  return `${baseId}-tab-${value}`;
}

/**
 * Выбрать вкладку.
 * @param {string} value - значение вкладки.
 */
function select(value: string): void {
  emit('update:modelValue', value);
}

/**
 * Стрелки, Home и End: выбрать соседнюю вкладку и перевести на неё фокус.
 * @param {KeyboardEvent} event - нажатие.
 * @param {number} index - номер вкладки, на которой фокус.
 */
async function handleKeydown(event: KeyboardEvent, index: number): Promise<void> {
  const last = props.tabs.length - 1;
  const next = {
    [KEYS.left]: index === 0 ? last : index - 1,
    [KEYS.right]: index === last ? 0 : index + 1,
    [KEYS.home]: 0,
    [KEYS.end]: last,
  }[event.key];
  if (next === undefined) return;

  event.preventDefault();
  select(props.tabs[next].value);
  await nextTick();
  buttons.value?.[next]?.focus();
}
</script>

<style lang="scss" module>
.VTabs {
  display: grid;
  grid-template-columns: minmax(0, 1fr); // широкое содержимое не распирает вкладки
  gap: var(--space-3);
}

.list {
  display: flex;
  gap: var(--space-1);
  border-bottom: var(--border-width) solid var(--base-100);
}

.tab {
  padding: var(--space-2) var(--space-3);
  margin-bottom: calc(-1 * var(--border-width)); // линия выбранной вкладки - поверх общей
  color: var(--base-700);
  cursor: pointer;
  background: none;
  border: 0;
  border-bottom: var(--focus-width) solid transparent;
  transition:
    color var(--default-transition),
    border-color var(--default-transition);

  @include text(small);

  &:hover {
    color: var(--primary-600);
  }

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: calc(-1 * var(--focus-width));
  }

  &._active {
    color: var(--primary-600);
    border-bottom-color: var(--primary-500);
    font-weight: 600;
  }
}
</style>
