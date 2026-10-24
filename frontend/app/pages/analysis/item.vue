<template>
  <div :class="$style.ItemPage">
    <h1 :class="$style.title">Товар</h1>
    <VCard>
      <ItemSearch :initial="choice?.query" @select="openItem" />
    </VCard>
    <ItemPanel v-if="choice" :query="choice.query" :all="choice.all" />
    <p v-else :class="$style.note">
      Найдите товар - покажу выручку, долю, сколько продано и как менялись продажи по месяцам.
    </p>
  </div>
</template>

<script setup lang="ts">
// Выбранный товар живёт в адресе (?q=...&all=true): работает «Назад» в браузере,
// а ссылку можно открыть из других разделов
import { computed } from 'vue';
import { definePageMeta, navigateTo, useHead, useRoute } from '#imports';
import { type ItemChoice, ItemSearch } from '~/features/search-item';
import { ROUTES } from '~/shared/config';
import { VCard } from '~/shared/ui';
import { ItemPanel } from '~/widgets/item';

definePageMeta({ middleware: 'prepared' });
useHead({ title: 'Товар - AI-аналитик' });

const route = useRoute();

const choice = computed<ItemChoice | null>(() => {
  const { q, all } = route.query;
  return typeof q === 'string' && q ? { query: q, all: all === 'true' } : null;
});

/**
 * Открыть товар: записываем выбор в адрес - страница покажет карточку.
 * @param {ItemChoice} item - товар или все подходящие.
 */
async function openItem(item: ItemChoice): Promise<void> {
  await navigateTo({
    path: ROUTES.item,
    query: { q: item.query, all: item.all ? 'true' : undefined },
  });
}
</script>

<style lang="scss" module>
.ItemPage {
  display: grid;
  gap: var(--space-4);
}

.title {
  @include text(h1);
}

.note {
  color: var(--base-700);
}
</style>
