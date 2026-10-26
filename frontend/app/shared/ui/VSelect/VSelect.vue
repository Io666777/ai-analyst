<template>
  <VFormField
    v-slot="{ id, describedBy, invalid }"
    :class="$style.VSelect"
    :label="label"
    :hint="hint"
    :error="error"
    :warning="warning"
    :required="required"
  >
    <div :class="$style.box">
      <select
        :id="id"
        :class="[$style.field, { [$style._error]: invalid, [$style._empty]: !modelValue }]"
        :name="name"
        :value="modelValue"
        :disabled="disabled"
        :required="required"
        :aria-invalid="invalid"
        :aria-describedby="describedBy"
        @change="handleChange"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </select>
    </div>
  </VFormField>
</template>

<script setup lang="ts">
/**
 * Выпадающий список на основе настоящего select: на телефоне открывается родной выбор системы,
 * клавиатура и экранный диктор работают сами.
 *
 * @example
 * <VSelect v-model="role" label="Роль колонки" :options="roles" placeholder="Выберите роль" />
 */
import { VFormField } from '../VFormField';
import type { SelectOption } from './types';

withDefaults(
  defineProps<{
    /** Выбранное значение (v-model). Пустая строка - ничего не выбрано. */
    modelValue?: string;
    /** Подпись над списком. */
    label: string;
    /** Варианты. */
    options: SelectOption[];
    /** Текст, пока ничего не выбрано. */
    placeholder?: string;
    /** Имя поля в форме. */
    name?: string;
    /** Подсказка под списком. */
    hint?: string;
    /** Текст ошибки - вместо подсказки, список подсвечивается. */
    error?: string;
    /** Обратить внимание (не ошибка): «проверьте». Вместо подсказки. */
    warning?: string;
    /** Список неактивен. */
    disabled?: boolean;
    /** Выбор обязателен - звёздочка у подписи. */
    required?: boolean;
  }>(),
  {
    modelValue: '',
    placeholder: undefined,
    name: undefined,
    hint: undefined,
    error: undefined,
    warning: undefined,
    disabled: false,
    required: false,
  },
);

const emit = defineEmits<{
  /** Новое выбранное значение. */
  'update:modelValue': [value: string];
}>();

/**
 * Передаёт выбранное значение наружу.
 * @param {Event} event - событие выбора.
 */
function handleChange(event: Event): void {
  emit('update:modelValue', (event.target as HTMLSelectElement).value);
}
</script>

<style lang="scss" module>
$arrow-size: 0.5rem;

.VSelect {
  min-width: 0; // в сетке список может сжиматься, а не распирать колонку
}

.box {
  position: relative;

  // Стрелка вниз - уголок из рамки, цвет из токенов
  &::after {
    position: absolute;
    top: 50%;
    right: var(--space-3);
    width: $arrow-size;
    height: $arrow-size;
    content: '';
    border-right: var(--focus-width) solid var(--base-500);
    border-bottom: var(--focus-width) solid var(--base-500);
    transform: translateY(-75%) rotate(45deg);
    pointer-events: none;
  }
}

.field {
  @include control;

  padding-right: var(--space-6); // место под стрелку
  cursor: pointer;
  appearance: none;

  @include ellipsis;

  // Пока ничего не выбрано - текст-подсказка серым
  &._empty {
    color: var(--base-500);
  }
}
</style>
