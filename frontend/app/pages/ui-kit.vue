<template>
  <section :class="$style.UiKitPage">
    <h1 :class="$style.title">Базовые компоненты</h1>
    <p :class="$style.lead">Служебная страница: все компоненты shared/ui во всех состояниях.</p>

    <section :class="$style.block">
      <h2 :class="$style.blockTitle">VButton</h2>
      <div v-for="variant in BUTTON_VARIANTS" :key="variant" :class="$style.row">
        <VButton :variant="variant">{{ variant }}</VButton>
        <VButton :variant="variant" :size="BUTTON_SIZES.small">small</VButton>
        <VButton :variant="variant" disabled>disabled</VButton>
        <VButton :variant="variant" :loading="isLoading" @click="handleLoadingDemo">
          {{ isLoading ? 'считаю...' : 'нажми - loading' }}
        </VButton>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { BUTTON_SIZES, BUTTON_VARIANTS, VButton } from '~/shared/ui';

const LOADING_DEMO_MS = 1500;

const isLoading = ref(false);

/** Показывает состояние загрузки на полторы секунды. */
function handleLoadingDemo(): void {
  isLoading.value = true;
  setTimeout(() => {
    isLoading.value = false;
  }, LOADING_DEMO_MS);
}
</script>

<style lang="scss" module>
.UiKitPage {
  display: grid;
  gap: 1.5rem;
}

.title {
  @include text(h1);
}

.lead {
  color: var(--base-700);
}

.block {
  display: grid;
  gap: 1rem;
  padding: 1.5rem;
  background: var(--white);
  border: 0.0625rem solid var(--base-100);
  border-radius: var(--radius);
}

.blockTitle {
  @include text(h2);
}

.row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}
</style>
