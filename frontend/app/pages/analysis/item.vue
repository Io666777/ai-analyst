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
import { computed, watch } from 'vue';
import type { RouteLocationRaw } from 'vue-router';
import { definePageMeta, navigateTo, useHead, useRoute } from '#imports';
import { useSessionState } from '~/entities/session';
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

// Последний открытый товар: ушли на другую вкладку и вернулись по ссылке «Товар» (без ?q=) -
// показываем его снова, а не пустой поиск
const lastChoice = useSessionState<ItemChoice | null>('item-choice', () => null);

watch(
  choice,
  value => {
    if (value) lastChoice.value = { ...value };
  },
  { immediate: true },
);

if (!choice.value && lastChoice.value) {
  navigateTo(itemLocation(lastChoice.value), { replace: true });
}

/**
 * Адрес страницы товара.
 * @param {ItemChoice} item - товар или все подходящие.
 * @returns {object} путь и параметры адреса.
 */
function itemLocation(item: ItemChoice): RouteLocationRaw {
  return { path: ROUTES.item, query: { q: item.query, all: item.all ? 'true' : undefined } };
}

/**
 * Открыть товар: записываем выбор в адрес - страница покажет карточку.
 * @param {ItemChoice} item - товар или все подходящие.
 */
async function openItem(item: ItemChoice): Promise<void> {
  await navigateTo(itemLocation(item));
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
