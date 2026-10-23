<template>
  <button
    :type="type"
    :class="classList"
    :disabled="isDisabled"
    :aria-busy="loading"
    @click="handleClick"
  >
    <span v-if="loading" :class="$style.spinner" aria-hidden="true" />
    <span :class="$style.text">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
/**
 * Базовая кнопка.
 * Пока идёт загрузка (loading) - показывает спиннер и не нажимается: двойной клик не отправит
 * запрос дважды.
 *
 * @example
 * <VButton :loading="isCounting" @click="handleForecast">Посчитать прогноз</VButton>
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, useCssModule } from 'vue';
import { BUTTON_SIZES, BUTTON_VARIANTS, type ButtonSize, type ButtonVariant } from './constants';

const props = withDefaults(
  defineProps<{
    /** Внешний вид: primary - главное действие, secondary - второстепенное, ghost - текстом. */
    variant?: ButtonVariant;
    /** Размер. */
    size?: ButtonSize;
    /** Тип кнопки в форме: submit отправляет форму. */
    type?: 'button' | 'submit';
    /** Кнопка неактивна. */
    disabled?: boolean;
    /** Идёт загрузка: спиннер, кнопка не нажимается. */
    loading?: boolean;
  }>(),
  {
    variant: BUTTON_VARIANTS.primary,
    size: BUTTON_SIZES.medium,
    type: 'button',
    disabled: false,
    loading: false,
  },
);

const emit = defineEmits<{
  /** Нажатие - только когда кнопка активна. */
  click: [event: MouseEvent];
}>();

const style = useCssModule();

const isDisabled = computed(() => props.disabled || props.loading);

const classList = computed(() => [
  style.VButton,
  style[`_${props.variant}`],
  style[`_${props.size}`],
  { [style._loading]: props.loading },
]);

/**
 * Передаёт нажатие наружу.
 * @param {MouseEvent} event - событие нажатия.
 */
function handleClick(event: MouseEvent): void {
  if (isDisabled.value) return;
  emit('click', event);
}
</script>

<style lang="scss" module>
.VButton {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: var(--border-width) solid transparent;
  border-radius: var(--radius);
  font-family: inherit;
  cursor: pointer;
  user-select: none;
  transition:
    background var(--default-transition),
    border-color var(--default-transition),
    color var(--default-transition);

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: var(--focus-width);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  &._loading:disabled {
    cursor: progress;
    opacity: 0.8;
  }

  // ---------- внешний вид ----------

  &._primary {
    color: var(--white);
    background: var(--primary-500);

    &:hover:not(:disabled) {
      background: var(--primary-600);
    }

    &:active:not(:disabled) {
      background: var(--primary-900);
    }
  }

  // Текст цветом - на тон темнее: --primary-500 на светлом фоне даёт контраст 4.49 при норме 4.5
  &._secondary {
    color: var(--primary-600);
    background: var(--white);
    border-color: var(--primary-300);

    &:hover:not(:disabled) {
      background: var(--primary-100);
      border-color: var(--primary-500);
    }

    &:active:not(:disabled) {
      background: var(--primary-300);
    }
  }

  &._ghost {
    color: var(--primary-600);
    background: transparent;

    &:hover:not(:disabled) {
      background: var(--primary-100);
    }

    &:active:not(:disabled) {
      color: var(--primary-900);
    }
  }

  // ---------- размер ----------

  &._medium {
    min-height: var(--control-height);
    padding: var(--space-2) var(--space-5);

    @include text(body);
  }

  &._small {
    min-height: var(--control-height-small);
    padding: var(--space-2) var(--space-3);

    @include text(small);
  }
}

.text {
  user-select: none;
}

.spinner {
  width: 1em;
  height: 1em;
  border: var(--focus-width) solid currentcolor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
