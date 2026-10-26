<template>
  <div :class="$style.ItemPage">
    <h1 :class="$style.title">Товар</h1>
    <div :class="$style.layout">
      <!-- Каталог слева (на телефоне - сверху), карточка товара - рядом -->
      <VCard :class="$style.catalog">
        <ItemCatalog :selected="choice && !choice.all ? choice.query : null" @select="openItem" />
      </VCard>
      <div :class="$style.detail">
        <ItemPanel v-if="choice" :query="choice.query" :all="choice.all" />
        <p v-else :class="$style.note">
          Выберите товар в списке - покажу выручку, долю, сколько продано и как менялись продажи
          по месяцам и дням.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Выбранный товар живёт в адресе (?q=...&all=true): работает «Назад» в браузере,
// а ссылку можно открыть из других разделов
import { computed, watch } from 'vue';
import type { RouteLocationRaw } from 'vue-router';
import { definePageMeta, navigateTo, useHead, useRoute } from '#imports';
import { useSessionState } from '~/entities/session';
import { ItemCatalog, type ItemChoice } from '~/features/search-item';
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
// показываем его снова, а не пустую карточку
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
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-4);
}

.title {
  @include text(h1);
}

// Каталог - колонка слева, карточка - справа; на узких экранах - друг под другом
.layout {
  display: grid;
  grid-template-columns: minmax(16rem, 22rem) minmax(0, 1fr);
  gap: var(--space-5);
  align-items: start;

  @include respond-to(mobile) {
    grid-template-columns: minmax(0, 1fr);
  }
}

// Каталог остаётся на экране, пока листаешь длинную карточку товара
.catalog {
  position: sticky;
  top: var(--space-4);

  @include respond-to(mobile) {
    position: static;
  }
}

.detail {
  min-width: 0;
}

.note {
  color: var(--base-700);
}
</style>
