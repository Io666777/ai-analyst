<template>
  <div :class="$style.ComparePage">
    <h1 :class="$style.title">Сравнение периодов</h1>
    <ComparePanel />
  </div>
</template>

<script setup lang="ts">
import { definePageMeta, useHead } from '#imports';
import { ComparePanel } from '~/widgets/compare';

definePageMeta({ middleware: 'prepared' });
useHead({ title: 'Сравнение периодов - AI-аналитик' });
</script>

<style lang="scss" module>
.ComparePage {
  display: grid;
  gap: var(--space-4);
}

.title {
  @include text(h1);
}
</style>
