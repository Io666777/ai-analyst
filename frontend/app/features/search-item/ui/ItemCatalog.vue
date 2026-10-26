<template>
  <div :class="$style.ItemCatalog">
    <form role="search" :class="$style.search" @submit.prevent="handleSubmit">
      <VFormField v-slot="{ id, describedBy }" label="Товар" hint="Начните вводить название или артикул">
        <input
          :id="id"
          v-model="query"
          :class="$style.input"
          type="search"
          autocomplete="off"
          :maxlength="QUERY_MAX_LENGTH"
          :aria-describedby="describedBy"
          :aria-controls="listId"
          @input="serverFound = null"
        >
      </VFormField>
    </form>

    <!-- Сколько подходит - диктор прочитает сам, когда число поменяется -->
    <div :class="$style.status" aria-live="polite">
      <p :class="$style.count">{{ countText }}</p>
      <VButton
        v-if="query.trim() && matched.length > 1"
        :variant="BUTTON_VARIANTS.ghost"
        :size="BUTTON_SIZES.small"
        @click="select({ query: query.trim(), all: true })"
      >
        Все вместе ({{ matched.length }})
      </VButton>
    </div>

    <VSpinner v-if="isLoading && !catalog" label="Загружаю список товаров..." show-label />
    <VAlert v-else-if="error" :variant="ALERT_VARIANTS.error">{{ error }}</VAlert>

    <template v-else-if="catalog">
      <ul v-if="visible.length" :id="listId" ref="list" :class="$style.list" aria-label="Товары">
        <li v-for="item in rows" :key="item.name">
          <button
            type="button"
            :class="[$style.row, { [$style._selected]: item.name === selected }]"
            :aria-current="item.name === selected ? 'true' : undefined"
            :data-name="item.name"
            @click="select({ query: item.name, all: false })"
          >
            <span :class="$style.name">
              {{ item.parts.before }}<mark :class="$style.mark">{{ item.parts.match }}</mark>{{ item.parts.after }}
            </span>
            <span :class="$style.value">{{ formatMoney(item.value, catalog.currency) }}</span>
            <span :class="$style.share">{{ formatPercent(item.share_percent, false) }}</span>
          </button>
        </li>
      </ul>

      <!-- По названию ничего: предлагаем искать по артикулу на сервере -->
      <div v-else :class="$style.empty">
        <template v-if="serverFound">
          <p v-if="!serverFound.total" :class="$style.count">
            Ни по названию, ни по артикулу «{{ serverFound.query }}» ничего не нашлось.
          </p>
          <ul v-else :class="$style.list" aria-label="Найдено по артикулу">
            <li v-for="name in serverFound.items" :key="name">
              <button type="button" :class="$style.row" @click="selectFound(name)">
                <span :class="$style.name">{{ name }}</span>
              </button>
            </li>
          </ul>
        </template>
        <template v-else>
          <p :class="$style.count">По названию ничего. Это артикул или код?</p>
          <VButton
            :variant="BUTTON_VARIANTS.secondary"
            :size="BUTTON_SIZES.small"
            :loading="isSearching"
            @click="searchServer"
          >
            Искать по артикулу
          </VButton>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Каталог товаров под поиском: виден весь список от самых продаваемых, по мере ввода
 * остаются только подходящие (совпадение выделено). Клик по строке - открыть товар.
 * Enter: подходит ровно один - открыть его; по названию ничего - искать по артикулу.
 *
 * @example
 * <ItemCatalog :selected="choice?.query" @select="openItem" />
 */
import { computed, nextTick, useId, useTemplateRef, watch } from 'vue';
import { formatMoney, formatNumber, formatPercent, pluralize, type WordForms } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_SIZES,
  BUTTON_VARIANTS,
  VAlert,
  VButton,
  VFormField,
  VSpinner,
} from '~/shared/ui';
import { splitMatch } from '../lib/split-match';
import type { ItemChoice } from '../model/item-choice';
import { QUERY_MAX_LENGTH, useItemCatalog, VISIBLE_LIMIT } from '../model/useItemCatalog';

const ITEM_FORMS: WordForms = { one: 'товар', few: 'товара', many: 'товаров' };

const props = withDefaults(
  defineProps<{
    /** Открытый товар - подсвечен в списке. */
    selected?: string | null;
  }>(),
  { selected: null },
);

const emit = defineEmits<{
  /** Выбран товар (или все подходящие вместе). */
  select: [choice: ItemChoice];
}>();

const {
  query,
  catalog,
  matched,
  visible,
  isLoading,
  error,
  serverFound,
  isSearching,
  searchServer,
} = useItemCatalog();

const listId = useId();
const list = useTemplateRef<HTMLElement>('list');

// Строки с разбивкой названия вокруг совпадения - совпавшая часть выделена
const rows = computed(() =>
  visible.value.map(item => ({ ...item, parts: splitMatch(item.name, query.value) })),
);

const countText = computed(() => {
  if (!catalog.value) return '';
  const total = matched.value.length;
  if (!query.value.trim()) {
    return `Всего ${pluralize(catalog.value.total, ITEM_FORMS)} - от самых продаваемых`;
  }
  if (!total) return '';
  const head = `Подходит: ${pluralize(total, ITEM_FORMS)}`;
  return total > VISIBLE_LIMIT ? `${head}, показаны первые ${formatNumber(VISIBLE_LIMIT)}` : head;
});

/**
 * Открыть товар.
 * @param {ItemChoice} choice - товар или все подходящие.
 */
function select(choice: ItemChoice): void {
  emit('select', choice);
}

/**
 * Открыть товар, найденный по артикулу: поле очищаем - снова виден весь каталог,
 * и в нём подсвечен открытый товар (а не пустой список «по названию ничего»).
 * @param {string} name - название товара.
 */
function selectFound(name: string): void {
  query.value = '';
  serverFound.value = null;
  select({ query: name, all: false });
}

/** Enter: подходит один - открыть; по названию ничего - искать по артикулу. */
async function handleSubmit(): Promise<void> {
  if (matched.value.length === 1) {
    select({ query: matched.value[0].name, all: false });
    return;
  }
  if (matched.value.length) return;
  const found = await searchServer();
  if (found?.total === 1) selectFound(found.items[0]);
}

// Открытый товар виден в списке: прокручиваем к нему (список прокручивается сам по себе)
watch(
  () => [props.selected, catalog.value] as const,
  async ([name]) => {
    if (!name) return;
    await nextTick();
    const row = list.value?.querySelector<HTMLElement>(`[data-name="${CSS.escape(name)}"]`);
    row?.scrollIntoView({ block: 'nearest' });
  },
  { immediate: true },
);
</script>

<style lang="scss" module>
.ItemCatalog {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-3);
}

.input {
  @include control;
}

.status {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  align-items: center;
  justify-content: space-between;
  min-height: var(--control-height-small);
}

.count {
  color: var(--base-700);

  @include text(small);
}

// Длинный каталог прокручивается внутри себя, поиск остаётся на месте
.list {
  max-height: 32rem;
  padding: 0;
  margin: 0;
  overflow-y: auto;
  list-style: none;
  border: var(--border-width) solid var(--base-100);
  border-radius: var(--radius);

  @include respond-to(mobile) {
    max-height: 16rem;
  }
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 3.5rem;
  gap: var(--space-2);
  align-items: baseline;
  width: 100%;
  padding: var(--space-2) var(--space-3);
  color: var(--base-900);
  text-align: left;
  cursor: pointer;
  background: none;
  border: 0;
  border-bottom: var(--border-width) solid var(--base-100);

  @include text(small);

  &:hover {
    background: var(--base-50);
  }

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: calc(-1 * var(--focus-width));
  }

  &._selected {
    background: var(--primary-100);
    font-weight: 600;
  }
}

.name {
  @include ellipsis;
}

.mark {
  font-weight: 700;
  color: inherit;
  background: none;
}

.value,
.share {
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.share {
  color: var(--base-500);
}

.empty {
  display: grid;
  gap: var(--space-2);
  justify-items: start;
}
</style>
