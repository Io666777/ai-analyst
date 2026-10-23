<template>
  <VFormField
    v-slot="{ id, describedBy, invalid }"
    :class="$style.VInput"
    :label="label"
    :hint="hint"
    :error="error"
    :required="required"
  >
    <input
      :id="id"
      :class="[$style.field, { [$style._error]: invalid }]"
      :type="type"
      :name="name"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :aria-invalid="invalid"
      :aria-describedby="describedBy"
      @input="handleInput"
    >
  </VFormField>
</template>

<script setup lang="ts">
/**
 * Поле ввода с подписью, подсказкой и ошибкой.
 * Само значение не проверяет - только показывает ошибку, которую передали снаружи:
 * что правильно, знает фича, которая использует поле.
 *
 * @example
 * <VInput v-model="query" label="Товар" hint="Название, его часть или артикул" />
 */
import { VFormField } from '../VFormField';
import { INPUT_TYPES, type InputType } from './constants';

withDefaults(
  defineProps<{
    /** Значение поля (v-model). */
    modelValue?: string | number;
    /** Подпись над полем - обязательна: placeholder её не заменяет. */
    label: string;
    /** Тип поля. */
    type?: InputType;
    /** Имя поля в форме. */
    name?: string;
    /** Пример значения внутри пустого поля. */
    placeholder?: string;
    /** Подсказка под полем. */
    hint?: string;
    /** Текст ошибки - показывается вместо подсказки, поле подсвечивается. */
    error?: string;
    /** Поле неактивно. */
    disabled?: boolean;
    /** Поле обязательно - звёздочка у подписи. */
    required?: boolean;
  }>(),
  {
    modelValue: '',
    type: INPUT_TYPES.text,
    name: undefined,
    placeholder: undefined,
    hint: undefined,
    error: undefined,
    disabled: false,
    required: false,
  },
);

const emit = defineEmits<{
  /** Новое значение поля. */
  'update:modelValue': [value: string];
}>();

/**
 * Передаёт новое значение наружу.
 * @param {Event} event - событие ввода.
 */
function handleInput(event: Event): void {
  emit('update:modelValue', (event.target as HTMLInputElement).value);
}
</script>

<style lang="scss" module>
.VInput {
  min-width: 0; // в сетке поле может сжиматься, а не распирать колонку
}

.field {
  @include control;

  &::placeholder {
    color: var(--base-500);
  }
}
</style>
