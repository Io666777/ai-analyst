<template>
  <div :class="$style.ForecastPage">
    <h1 :class="$style.title">Прогноз продаж</h1>
    <ForecastPanel />
  </div>
</template>

<script setup lang="ts">
import { definePageMeta, useHead } from '#imports';
import { ForecastPanel } from '~/widgets/forecast';

definePageMeta({ middleware: 'prepared' });
useHead({ title: 'Прогноз продаж - AI-аналитик' });
</script>

<style lang="scss" module>
.ForecastPage {
  display: grid;
  gap: var(--space-4);
}

.title {
  @include text(h1);
}
</style>
