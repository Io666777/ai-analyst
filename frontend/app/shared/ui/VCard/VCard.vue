<template>
  <section :class="$style.VCard" :aria-labelledby="title ? titleId : undefined">
    <header v-if="title || $slots.actions" :class="$style.header">
      <component :is="`h${titleLevel}`" v-if="title" :id="titleId" :class="$style.title">
        {{ title }}
      </component>
      <div v-if="$slots.actions" :class="$style.actions">
        <slot name="actions" />
      </div>
    </header>

    <slot />
  </section>
</template>

<script setup lang="ts">
/**
 * Белая карточка - контейнер для блока на экране: заголовок, кнопки справа от него, содержимое.
 *
 * @example
 * <VCard title="Выручка по месяцам">
 *   <template #actions><VButton variant="ghost">Скачать</VButton></template>
 *   <VChart ... />
 * </VCard>
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { useId } from 'vue';

withDefaults(
  defineProps<{
    /** Заголовок карточки. */
    title?: string;
    /** Уровень заголовка: 2 - блок страницы, 3 - блок внутри блока. Важно для структуры страницы. */
    titleLevel?: 2 | 3;
  }>(),
  {
    title: undefined,
    titleLevel: 2,
  },
);

defineSlots<{
  /** Содержимое карточки. */
  default: () => unknown;
  /** Кнопки справа от заголовка. */
  actions?: () => unknown;
}>();

const titleId = useId();
</script>

<style lang="scss" module>
.VCard {
  display: grid;
  gap: var(--space-4);
  min-width: 0;
  padding: var(--space-5);
  background: var(--white);
  border: var(--border-width) solid var(--base-100);
  border-radius: var(--radius-large);
  box-shadow: var(--shadow-small);

  @include respond-to(mobile) {
    padding: var(--space-4);
  }
}

.header {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
  justify-content: space-between;
}

.title {
  @include text(h3);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
