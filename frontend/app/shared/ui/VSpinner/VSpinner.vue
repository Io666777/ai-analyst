<template>
  <span
    :class="classList"
    :role="decorative ? undefined : 'status'"
    :aria-hidden="decorative || undefined"
  >
    <span :class="$style.circle" />
    <span v-if="!decorative" :class="label && showLabel ? $style.label : $style.hiddenLabel">
      {{ label }}
    </span>
  </span>
</template>

<script setup lang="ts">
/**
 * Индикатор загрузки. Цвет - от текста вокруг (currentColor): в синей кнопке белый, в блоке - синий.
 * Диктор читает подпись (role="status"); decorative - только картинка, когда о загрузке
 * уже сообщает что-то другое (например, aria-busy у кнопки).
 *
 * @example
 * <VSpinner label="Считаю прогноз..." show-label />
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, useCssModule } from 'vue';
import { SPINNER_SIZES, type SpinnerSize } from './constants';

const props = withDefaults(
  defineProps<{
    /** Размер. */
    size?: SpinnerSize;
    /** Что загружается - для диктора, а с showLabel - и на экране. */
    label?: string;
    /** Показать подпись рядом с кружком. */
    showLabel?: boolean;
    /** Только картинка, без сообщения диктору. */
    decorative?: boolean;
  }>(),
  {
    size: SPINNER_SIZES.medium,
    label: 'Загрузка...',
    showLabel: false,
    decorative: false,
  },
);

const style = useCssModule();

const classList = computed(() => [style.VSpinner, style[`_${props.size}`]]);
</script>

<style lang="scss" module>
.VSpinner {
  display: inline-flex;
  gap: var(--space-2);
  align-items: center;
  color: inherit;

  &._small {
    --spinner-size: 1em;
  }

  &._medium {
    --spinner-size: 1.5rem;
  }

  &._large {
    --spinner-size: 2.5rem;
  }
}

.circle {
  flex-shrink: 0;
  width: var(--spinner-size);
  height: var(--spinner-size);
  border: var(--focus-width) solid currentcolor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;

  // Кто попросил систему меньше анимаций - кружок крутится медленно
  @media (prefers-reduced-motion: reduce) {
    animation-duration: 2s;
  }
}

.label {
  color: var(--base-700);

  @include text(small);
}

.hiddenLabel {
  @include visually-hidden;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
