<template>
  <div :class="$style.OverviewPage">
    <h1 :class="$style.title">Обзор продаж</h1>
    <OverviewPanel />
  </div>
</template>

<script setup lang="ts">
import { definePageMeta, useHead } from '#imports';
import { OverviewPanel } from '~/widgets/overview';

definePageMeta({ middleware: 'prepared' });
useHead({ title: 'Обзор продаж - AI-аналитик' });
</script>

<style lang="scss" module>
.OverviewPage {
  display: grid;
  gap: var(--space-4);
}

.title {
  @include text(h1);
}
</style>
