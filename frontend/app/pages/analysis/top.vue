<template>
  <div :class="$style.TopPage">
    <h1 :class="$style.title">Что продаётся лучше всего</h1>
    <TopPanel />
  </div>
</template>

<script setup lang="ts">
import { definePageMeta, useHead } from '#imports';
import { TopPanel } from '~/widgets/top';

definePageMeta({ middleware: 'prepared' });
useHead({ title: 'Топ продаж - AI-аналитик' });
</script>

<style lang="scss" module>
.TopPage {
  display: grid;
  gap: var(--space-4);
}

.title {
  @include text(h1);
}
</style>
