<template>
  <label :class="classList">
    <input
      :class="$style.input"
      type="checkbox"
      :name="name"
      :checked="modelValue"
      :disabled="disabled"
      @change="handleChange"
    >
    <span :class="$style.box" aria-hidden="true" />
    <span :class="$style.text">
      <slot>{{ label }}</slot>
    </span>
  </label>
</template>

<script setup lang="ts">
/**
 * Флажок на основе настоящего checkbox: клик по подписи тоже переключает,
 * клавиатура (пробел) и экранный диктор работают сами.
 *
 * @example
 * <VCheckbox v-model="worst" label="Худшие вместо лучших" />
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, useCssModule } from 'vue';

const props = withDefaults(
  defineProps<{
    /** Отмечен ли флажок (v-model). */
    modelValue?: boolean;
    /** Подпись. Можно передать и через слот - например, с выделением части текста. */
    label?: string;
    /** Имя поля в форме. */
    name?: string;
    /** Флажок неактивен. */
    disabled?: boolean;
  }>(),
  {
    modelValue: false,
    label: undefined,
    name: undefined,
    disabled: false,
  },
);

const emit = defineEmits<{
  /** Новое состояние флажка. */
  'update:modelValue': [value: boolean];
}>();

const style = useCssModule();

const classList = computed(() => [style.VCheckbox, { [style._disabled]: props.disabled }]);

/**
 * Передаёт новое состояние наружу.
 * @param {Event} event - событие переключения.
 */
function handleChange(event: Event): void {
  emit('update:modelValue', (event.target as HTMLInputElement).checked);
}
</script>

<style lang="scss" module>
$box-size: 1.125rem;

.VCheckbox {
  display: inline-flex;
  gap: var(--space-2);
  align-items: flex-start;
  padding: var(--space-1) 0;
  cursor: pointer;

  &._disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
}

// Настоящий checkbox невидим, но остаётся для клавиатуры и диктора
.input {
  @include visually-hidden;
}

// Нарисованный квадратик
.box {
  position: relative;
  flex-shrink: 0;
  width: $box-size;
  height: $box-size;
  margin-top: 0.1875rem; // по центру первой строки текста
  background: var(--white);
  border: var(--focus-width) solid var(--base-500);
  border-radius: var(--radius-small);
  transition:
    background var(--default-transition),
    border-color var(--default-transition);

  // Галочка - уголок из рамки, появляется, когда флажок отмечен
  &::after {
    position: absolute;
    top: 0.0625rem;
    left: 0.3125rem;
    width: 0.3125rem;
    height: 0.625rem;
    content: '';
    border-right: var(--focus-width) solid var(--white);
    border-bottom: var(--focus-width) solid var(--white);
    opacity: 0;
    transform: rotate(45deg);
  }

  .VCheckbox:not(._disabled):hover & {
    border-color: var(--primary-500);
  }

  .input:checked + & {
    background: var(--primary-500);
    border-color: var(--primary-500);

    &::after {
      opacity: 1;
    }
  }

  .input:focus-visible + & {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: var(--focus-width);
  }
}

.text {
  color: var(--base-900);
  user-select: none;

  @include text(body);
}
</style>
