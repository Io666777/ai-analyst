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

    <section :class="$style.block">
      <h2 :class="$style.blockTitle">VInput</h2>
      <div :class="$style.grid">
        <VInput
          v-model="query"
          label="Товар"
          :type="INPUT_TYPES.search"
          placeholder="Например, пиво"
          hint="Название, его часть или артикул"
        />
        <VInput v-model="currency" label="Валюта" required :error="currencyError" />
        <VInput v-model="periodStart" label="Период с" :type="INPUT_TYPES.date" />
        <VInput model-value="shop.xlsx" label="Файл" disabled />
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { BUTTON_SIZES, BUTTON_VARIANTS, INPUT_TYPES, VButton, VInput } from '~/shared/ui';

const LOADING_DEMO_MS = 1500;

const isLoading = ref(false);
const query = ref('');
const currency = ref('');
const periodStart = ref('2026-09-01');

// Пример ошибки: валюта обязательна
const currencyError = computed(() => (currency.value.trim() ? '' : 'Укажите валюту: р., $, £...'));

let loadingTimer: ReturnType<typeof setTimeout> | undefined;

/** Показывает состояние загрузки на полторы секунды. */
function handleLoadingDemo(): void {
  isLoading.value = true;
  loadingTimer = setTimeout(() => {
    isLoading.value = false;
  }, LOADING_DEMO_MS);
}

onBeforeUnmount(() => clearTimeout(loadingTimer));
</script>

<style lang="scss" module>
.UiKitPage {
  display: grid;
  gap: var(--space-5);
}

.title {
  @include text(h1);
}

.lead {
  color: var(--base-700);
}

.block {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--white);
  border: var(--border-width) solid var(--base-100);
  border-radius: var(--radius);

  @include respond-to(mobile) {
    padding: var(--space-4);
  }
}

.blockTitle {
  @include text(h2);
}

.row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: var(--space-4);
}
</style>
