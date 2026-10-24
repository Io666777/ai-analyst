<template>
  <form :class="$style.ItemSearch" role="search" @submit.prevent="handleSubmit">
    <div :class="$style.row">
      <VFormField
        v-slot="{ id, describedBy, invalid }"
        :class="$style.field"
        label="Товар"
        hint="Начните вводить название или артикул"
        :error="error ?? undefined"
      >
        <div :class="$style.combo">
          <input
            :id="id"
            v-model="query"
            :class="[$style.input, { [$style._error]: invalid }]"
            type="search"
            role="combobox"
            autocomplete="off"
            aria-autocomplete="list"
            :aria-expanded="isListShown"
            :aria-controls="listId"
            :aria-activedescendant="activeOptionId"
            :aria-invalid="invalid"
            :aria-describedby="describedBy"
            :maxlength="QUERY_MAX_LENGTH"
            @input="isOpen = true"
            @focus="isOpen = true"
            @blur="isOpen = false"
            @keydown="handleKeydown"
          >

          <div v-show="isListShown" :class="$style.dropdown">
            <ul :id="listId" :class="$style.list" role="listbox" aria-label="Подходящие товары">
              <!-- mousedown.prevent: поле не теряет фокус, и клик успевает выбрать вариант -->
              <li
                v-for="(option, index) in options"
                :id="optionId(index)"
                :key="option.key"
                :class="[$style.option, { [$style._active]: index === activeIndex }]"
                role="option"
                :aria-selected="index === activeIndex"
                @mousedown.prevent
                @click="select(option.choice)"
                @mousemove="activeIndex = index"
              >
                <template v-if="option.choice.all">
                  <span :class="$style.all">{{ option.label }}</span>
                </template>
                <template v-else>
                  {{ option.parts.before }}<mark :class="$style.mark">{{ option.parts.match }}</mark>{{ option.parts.after }}
                </template>
              </li>
            </ul>
            <p v-if="footerText" :class="$style.footer">{{ footerText }}</p>
          </div>
        </div>
      </VFormField>

      <VButton type="submit" :loading="isLoading" :class="$style.submit">Найти</VButton>
    </div>

    <!-- Для диктора: сколько нашлось - прочитает сам, когда число поменяется -->
    <p :class="$style.status" aria-live="polite">{{ statusText }}</p>
  </form>
</template>

<script setup lang="ts">
/**
 * Поиск товара с выпадающими подсказками: печатаешь «с» - под полем «Снеки», «Соусы»...
 * Совпавшая часть выделена. Стрелки ↑↓ - выбор, Enter - открыть, Esc - закрыть список.
 * Нашёлся ровно один - Enter сразу открывает его. Несколько - можно смотреть их вместе.
 *
 * @example
 * <ItemSearch :initial="route.query.q" @select="openItem" />
 */
import { computed, ref, useId, watch } from 'vue';
import { pluralize, type WordForms } from '~/shared/lib';
import { VButton, VFormField } from '~/shared/ui';
import { type MatchParts, splitMatch } from '../lib/split-match';
import type { ItemChoice } from '../model/item-choice';
import { QUERY_MAX_LENGTH, useItemSearch } from '../model/useItemSearch';

const ITEM_FORMS: WordForms = { one: 'товар', few: 'товара', many: 'товаров' };
const KEYS = { down: 'ArrowDown', up: 'ArrowUp', enter: 'Enter', escape: 'Escape' } as const;

interface Option {
  key: string;
  label: string;
  parts: MatchParts;
  choice: ItemChoice;
}

const props = withDefaults(
  defineProps<{
    /** Запрос, с которого начать: например, из адреса страницы. */
    initial?: string;
  }>(),
  { initial: '' },
);

const emit = defineEmits<{
  /** Выбран товар (или все подходящие вместе). */
  select: [choice: ItemChoice];
}>();

const { query, found, isLoading, error, searchNow, reset, replaceQuery } = useItemSearch(
  props.initial,
);

const listId = useId();
const isOpen = ref(false);
const activeIndex = ref(-1);

// Стёрли запрос - старые подсказки больше не к месту
const suggestions = computed(() => (query.value.trim() ? found.value : null));

const options = computed<Option[]>(() => {
  if (!suggestions.value) return [];
  const { items, total, query: text } = suggestions.value;
  const list: Option[] = items.map(name => ({
    key: name,
    label: name,
    parts: splitMatch(name, text),
    choice: { query: name, all: false },
  }));
  if (total > 1) {
    list.push({
      key: '__all__',
      label: `Все подходящие вместе (${total})`,
      parts: { before: '', match: '', after: '' },
      choice: { query: text, all: true },
    });
  }
  return list;
});

const isListShown = computed(() => isOpen.value && Boolean(suggestions.value));
const activeOptionId = computed(() =>
  isListShown.value && activeIndex.value >= 0 ? optionId(activeIndex.value) : undefined,
);

const footerText = computed(() => {
  if (!suggestions.value) return '';
  const { items, total, query: text } = suggestions.value;
  if (!total) return `Ничего похожего на «${text}» не нашлось`;
  if (items.length < total) return `Показаны первые ${items.length} из ${total} - уточните запрос`;
  return '';
});

const statusText = computed(() =>
  suggestions.value ? `Нашлось: ${pluralize(suggestions.value.total, ITEM_FORMS)}` : '',
);

// Пришли новые подсказки - ни одна ещё не выбрана стрелками
watch(options, () => {
  activeIndex.value = -1;
});

// Открыли другой товар по ссылке или кнопкой «Назад» - в поле его название
watch(() => props.initial, replaceQuery);

/**
 * id варианта в списке - для aria-activedescendant.
 * @param {number} index - номер варианта.
 * @returns {string} id.
 */
function optionId(index: number): string {
  return `${listId}-option-${index}`;
}

/**
 * Выбор: сообщаем наверх, список закрываем.
 * @param {ItemChoice} choice - товар или все подходящие.
 */
function select(choice: ItemChoice): void {
  reset();
  isOpen.value = false;
  emit('select', choice);
}

/**
 * Стрелки, Enter и Esc в поле.
 * @param {KeyboardEvent} event - нажатие клавиши.
 */
function handleKeydown(event: KeyboardEvent): void {
  const count = options.value.length;

  if (event.key === KEYS.down || event.key === KEYS.up) {
    if (!count) return;
    event.preventDefault();
    isOpen.value = true;
    const step = event.key === KEYS.down ? 1 : -1;
    activeIndex.value = (activeIndex.value + step + count) % count;
    return;
  }

  if (event.key === KEYS.enter && isListShown.value && activeIndex.value >= 0) {
    event.preventDefault(); // не отправлять форму - выбран вариант из списка
    select(options.value[activeIndex.value].choice);
    return;
  }

  if (event.key === KEYS.escape && isListShown.value) {
    event.preventDefault(); // не стирать поле - только закрыть список
    isOpen.value = false;
  }
}

/** «Найти» или Enter без выбранного варианта: искать сразу; нашёлся ровно один - он и открыт. */
async function handleSubmit(): Promise<void> {
  const result = await searchNow();
  if (result?.total === 1) select({ query: result.items[0], all: false });
  else isOpen.value = true;
}
</script>

<style lang="scss" module>
.ItemSearch {
  display: grid;
}

.row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-3);
  align-items: flex-start;
}

.field {
  flex: 1 1 18rem;
  min-width: 0;
}

// Кнопка - на одной линии с полем, а не с подписью над ним:
// сдвиг = строка подписи (text(small): 0.875rem × 1.4) + отступ между подписью и полем
.submit {
  margin-top: calc(0.875rem * 1.4 + var(--space-1));

  // На телефоне кнопка уходит под поле - выравнивать не с чем
  @include respond-to(mobile) {
    margin-top: 0;
  }
}

// Список подсказок - поверх страницы, сразу под полем
.combo {
  position: relative;
}

.input {
  @include control;
}

.dropdown {
  position: absolute;
  top: calc(100% + var(--space-1));
  right: 0;
  left: 0;
  z-index: var(--z-dropdown);
  overflow: hidden;
  background: var(--white);
  border: var(--border-width) solid var(--base-300);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.list {
  max-height: 18rem;
  padding: var(--space-1) 0;
  margin: 0;
  overflow-y: auto;
  list-style: none;
}

.option {
  padding: var(--space-2) var(--space-3);
  color: var(--base-900);
  cursor: pointer;

  @include text(body);

  &._active {
    background: var(--primary-100);
  }
}

.mark {
  font-weight: 700;
  color: inherit;
  background: none;
}

.all {
  color: var(--primary-600);
}

.footer {
  padding: var(--space-2) var(--space-3);
  color: var(--base-700);
  border-top: var(--border-width) solid var(--base-100);

  @include text(small);
}

.status {
  @include visually-hidden;
}
</style>
