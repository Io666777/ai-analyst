<template>
  <div :class="classList" :role="variant === ALERT_VARIANTS.error ? 'alert' : 'status'">
    <p v-if="title" :class="$style.title">{{ title }}</p>
    <div :class="$style.content">
      <slot />
    </div>
    <div v-if="$slots.actions" :class="$style.actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Сообщение: сведения, успех, предупреждение или ошибка.
 * Ошибку диктор читает сразу (role="alert"), остальное - когда освободится (role="status").
 *
 * @example
 * <VAlert :variant="ALERT_VARIANTS.error" title="Сессия устарела">
 *   Загрузите файл заново
 *   <template #actions><VButton>Загрузить</VButton></template>
 * </VAlert>
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, useCssModule } from 'vue';
import { ALERT_VARIANTS, type AlertVariant } from './constants';

const props = withDefaults(
  defineProps<{
    /** Вид сообщения. */
    variant?: AlertVariant;
    /** Заголовок жирным. */
    title?: string;
  }>(),
  {
    variant: ALERT_VARIANTS.info,
    title: undefined,
  },
);

defineSlots<{
  /** Текст сообщения. */
  default?: () => unknown;
  /** Кнопки под текстом: "загрузить заново", "повторить". */
  actions?: () => unknown;
}>();

const style = useCssModule();

const classList = computed(() => [style.VAlert, style[`_${props.variant}`]]);
</script>

<style lang="scss" module>
$accent-width: 0.25rem;

.VAlert {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  color: var(--base-900);
  border-left: $accent-width solid;
  border-radius: var(--radius);

  @include text(small);

  &._info {
    background: var(--primary-100);
    border-left-color: var(--primary-500);
  }

  &._success {
    background: var(--success-100);
    border-left-color: var(--success-500);
  }

  &._warning {
    background: var(--warning-100);
    border-left-color: var(--warning-500);
  }

  &._error {
    background: var(--error-100);
    border-left-color: var(--error-500);
  }
}

.title {
  font-weight: 600;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-2);
}
</style>
