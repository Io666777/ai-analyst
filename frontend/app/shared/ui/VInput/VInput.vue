<template>
  <div :class="classList">
    <label :for="inputId" :class="$style.label">
      {{ label }}
      <span v-if="required" :class="$style.required" aria-hidden="true">*</span>
    </label>

    <input
      :id="inputId"
      :class="$style.field"
      :type="type"
      :name="name"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :aria-invalid="Boolean(error)"
      :aria-describedby="message ? messageId : undefined"
      @input="handleInput"
    >

    <p v-if="error" :id="messageId" :class="$style.error" role="alert">{{ error }}</p>
    <p v-else-if="hint" :id="messageId" :class="$style.hint">{{ hint }}</p>
  </div>
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
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, useCssModule, useId } from 'vue';
import { INPUT_TYPES, type InputType } from './constants';

const props = withDefaults(
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

const style = useCssModule();

// Свой id у каждого поля: клик по подписи ставит курсор в поле, диктор читает подсказку
const inputId = useId();
const messageId = `${inputId}-message`;

const message = computed(() => props.error || props.hint);

const classList = computed(() => [
  style.VInput,
  {
    [style._error]: Boolean(props.error),
    [style._disabled]: props.disabled,
  },
]);

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
  display: grid;
  align-content: start; // без подсказки поле не "сползает" вниз в ряду с соседями
  gap: var(--space-1);
}

.label {
  color: var(--base-700);
  user-select: none;

  @include text(small);
}

.required {
  color: var(--error-500);
}

.field {
  width: 100%;
  height: var(--control-height); // поле даты браузер иначе делает выше остальных
  padding: var(--space-2) var(--space-3);
  background: var(--white);
  border: var(--border-width) solid var(--base-300);
  border-radius: var(--radius);
  transition: border-color var(--default-transition);

  @include text(body);

  &::placeholder {
    color: var(--base-500);
  }

  &:hover:not(:disabled) {
    border-color: var(--base-500);
  }

  &:focus-visible {
    border-color: var(--primary-500);
    outline: var(--focus-width) solid var(--primary-100);
  }

  &:disabled {
    color: var(--base-500);
    cursor: not-allowed;
    background: var(--base-100);
  }

  .VInput._error & {
    border-color: var(--error-500);

    &:focus-visible {
      outline-color: var(--error-100);
    }
  }
}

.hint {
  color: var(--base-500);

  @include text(caption);
}

.error {
  color: var(--error-500);

  @include text(caption);
}
</style>
