<template>
  <VFormField
    v-slot="{ id, describedBy, invalid }"
    :class="$style.VDateRange"
    :label="label"
    :hint="hint"
    :error="error"
  >
    <div ref="root" :class="$style.root">
      <button
        :id="id"
        ref="field"
        type="button"
        :class="[$style.field, { [$style._error]: invalid, [$style._empty]: !hasValue }]"
        aria-haspopup="dialog"
        :aria-expanded="isOpen"
        :aria-invalid="invalid"
        :aria-describedby="describedBy"
        @click="toggle"
      >
        <span :class="$style.value">{{ fieldText }}</span>
        <span :class="$style.icon" aria-hidden="true" />
      </button>

      <div
        v-if="isOpen"
        :class="$style.popover"
        role="dialog"
        :aria-label="`${label}: выбор периода`"
        @keydown.esc.stop="close"
      >
        <div :class="$style.header">
          <button type="button" :class="$style.nav" aria-label="Предыдущий месяц" @click="shiftMonth(-1)">
            ‹
          </button>
          <span :class="$style.month" aria-live="polite">{{ monthTitle }}</span>
          <button type="button" :class="$style.nav" aria-label="Следующий месяц" @click="shiftMonth(1)">
            ›
          </button>
        </div>

        <div :class="$style.weekdays" aria-hidden="true">
          <span v-for="day in WEEKDAYS" :key="day">{{ day }}</span>
        </div>

        <!-- touch-action: none - пока тянешь пальцем по дням, страница не прокручивается -->
        <div ref="grid" :class="$style.grid" @pointermove="handlePointerMove">
          <button
            v-for="day in days"
            :key="day.iso"
            type="button"
            :data-day="day.iso"
            :class="dayClasses(day)"
            :tabindex="day.iso === focusedDay ? 0 : -1"
            :aria-label="dayLabel(day.iso)"
            :aria-pressed="isInRange(day.iso)"
            @pointerdown="handlePointerDown($event, day.iso)"
            @keydown="handleDayKeydown($event, day.iso)"
          >
            {{ day.date }}
          </button>
        </div>

        <div :class="$style.footer">
          <p :class="$style.tip">{{ tipText }}</p>
          <button v-if="clearable && hasValue" type="button" :class="$style.clear" @click="clear">
            {{ clearLabel }}
          </button>
        </div>
      </div>
    </div>
  </VFormField>
</template>

<script setup lang="ts">
/**
 * Выбор периода в своём календаре: протянуть мышью или пальцем по дням - или нажать
 * начало и конец (так можно и через границу месяца). Клавиатура: стрелки - дни и недели,
 * PageUp / PageDown - месяцы, Enter или пробел - как клик, Esc - закрыть.
 * Колесо мыши ничего не крутит - в отличие от системного поля даты.
 *
 * @example
 * <VDateRange v-model="period" label="Было" :max="dataEnd" />
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, nextTick, onBeforeUnmount, ref, useCssModule, useTemplateRef, watch } from 'vue';
import { LOCALE } from '~/shared/config';
import { capitalize, formatDate, formatMonth, parseIsoDate, toIsoDate } from '~/shared/lib';
import { VFormField } from '../VFormField';
import type { DateRange } from './types';

const props = withDefaults(
  defineProps<{
    /** Период (v-model): даты "2026-09-01"; пустые - период не выбран. */
    modelValue: DateRange;
    /** Подпись над полем. */
    label: string;
    /** Текст, пока период не выбран. */
    placeholder?: string;
    /** Подсказка под полем. */
    hint?: string;
    /** Текст ошибки - вместо подсказки. */
    error?: string;
    /** Первый день данных: дни раньше - бледные (выбрать можно, но данных там нет). */
    min?: string;
    /** Последний день данных; с него календарь открывается, если период не выбран. */
    max?: string;
    /** Можно сбросить период (кнопка внизу календаря). */
    clearable?: boolean;
    /** Подпись кнопки сброса. */
    clearLabel?: string;
  }>(),
  {
    placeholder: 'Выберите период',
    hint: undefined,
    error: undefined,
    min: undefined,
    max: undefined,
    clearable: false,
    clearLabel: 'Сбросить',
  },
);

const emit = defineEmits<{
  /** Выбран период. */
  'update:modelValue': [value: DateRange];
}>();

interface Day {
  iso: string;
  date: number;
  /** День соседнего месяца - в сетке для ровных недель. */
  outside: boolean;
}

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const GRID_DAYS = 42; // 6 недель - сетка одной высоты для любого месяца
const KEY_STEPS: Record<string, number> = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
const MONTH_KEYS: Record<string, number> = { PageUp: -1, PageDown: 1 };

const style = useCssModule();
const root = useTemplateRef<HTMLElement>('root');
const field = useTemplateRef<HTMLButtonElement>('field');
const grid = useTemplateRef<HTMLElement>('grid');

const isOpen = ref(false);
/** Первое число показанного месяца. */
const viewMonth = ref(startOfMonth(initialDay()));
/** День с фокусом клавиатуры. */
const focusedDay = ref(initialDay());
/** Начало периода после первого клика - ждём второй. */
const pendingStart = ref<string | null>(null);
/** Тянут мышью или пальцем: откуда. */
const dragStart = ref<string | null>(null);
/** День под курсором - для подсветки будущего периода. */
const hoverDay = ref<string | null>(null);

const hasValue = computed(() => Boolean(props.modelValue.from && props.modelValue.to));

const fieldText = computed(() => {
  const { from, to } = props.modelValue;
  if (!from || !to) return props.placeholder;
  return from === to ? formatDate(from) : `${formatDate(from)} - ${formatDate(to)}`;
});

const monthTitle = computed(() => capitalize(formatMonth(viewMonth.value)));

const tipText = computed(() =>
  pendingStart.value
    ? `С ${formatDate(pendingStart.value)} - теперь нажмите последний день`
    : 'Протяните по дням или нажмите первый и последний день',
);

const days = computed<Day[]>(() => {
  const first = parseIsoDate(viewMonth.value);
  const offset = (first.getDay() + 6) % 7; // понедельник - первый день недели
  return Array.from({ length: GRID_DAYS }, (_, index) => {
    const day = new Date(first.getFullYear(), first.getMonth(), 1 - offset + index);
    return { iso: toIsoDate(day), date: day.getDate(), outside: day.getMonth() !== first.getMonth() };
  });
});

/** Какой период подсвечен сейчас: тянут, ждут второй клик или уже выбранный. */
const shownRange = computed<DateRange | null>(() => {
  const start = dragStart.value ?? pendingStart.value;
  if (start) return ordered(start, hoverDay.value ?? start);
  return hasValue.value ? props.modelValue : null;
});

const dayFormat = new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'long', year: 'numeric' });

/**
 * С какого дня открыть календарь: начало периода, последний день данных или сегодня.
 * @returns {string} день "2026-09-30".
 */
function initialDay(): string {
  return props.modelValue.from || props.max || toIsoDate(new Date());
}

/**
 * Первое число месяца этого дня.
 * @param {string} iso - день.
 * @returns {string} "2026-09-01".
 */
function startOfMonth(iso: string): string {
  const day = parseIsoDate(iso);
  return toIsoDate(new Date(day.getFullYear(), day.getMonth(), 1));
}

/**
 * Период по порядку: начало раньше конца, как бы ни тянули.
 * @param {string} a - один край.
 * @param {string} b - другой край.
 * @returns {DateRange} период.
 */
function ordered(a: string, b: string): DateRange {
  return a <= b ? { from: a, to: b } : { from: b, to: a };
}

/**
 * День входит в подсвеченный период.
 * @param {string} iso - день.
 * @returns {boolean} да - подсвечен.
 */
function isInRange(iso: string): boolean {
  const range = shownRange.value;
  return Boolean(range && iso >= range.from && iso <= range.to);
}

/**
 * Классы дня: края и середина периода, соседний месяц, вне данных.
 * @param {Day} day - день сетки.
 * @returns {unknown[]} классы.
 */
function dayClasses(day: Day): unknown[] {
  const range = shownRange.value;
  const outsideData = (props.min && day.iso < props.min) || (props.max && day.iso > props.max);
  return [
    style.day,
    {
      [style._inRange]: isInRange(day.iso),
      [style._edge]: range && (day.iso === range.from || day.iso === range.to),
      [style._outside]: day.outside,
      [style._noData]: outsideData,
    },
  ];
}

/**
 * Подпись дня для экранного диктора: «15 сентября 2026».
 * @param {string} iso - день.
 * @returns {string} подпись.
 */
function dayLabel(iso: string): string {
  return dayFormat.format(parseIsoDate(iso));
}

/** Открыть или закрыть календарь. */
async function toggle(): Promise<void> {
  if (isOpen.value) {
    close();
    return;
  }
  focusedDay.value = initialDay();
  viewMonth.value = startOfMonth(focusedDay.value);
  isOpen.value = true;
  await focusDay(focusedDay.value);
}

/** Закрыть без выбора: недоделанный период забываем, фокус - обратно на поле. */
function close(): void {
  isOpen.value = false;
  pendingStart.value = null;
  dragStart.value = null;
  hoverDay.value = null;
  field.value?.focus();
}

/**
 * Период выбран: сообщаем наверх и закрываем.
 * @param {string} a - один край.
 * @param {string} b - другой край.
 */
function commit(a: string, b: string): void {
  emit('update:modelValue', ordered(a, b));
  close();
}

/** Сбросить период (например, «за всё время»). */
function clear(): void {
  emit('update:modelValue', { from: '', to: '' });
  close();
}

/**
 * Листать месяцы.
 * @param {number} step - на сколько месяцев: -1 назад, 1 вперёд.
 */
function shiftMonth(step: number): void {
  const month = parseIsoDate(viewMonth.value);
  viewMonth.value = toIsoDate(new Date(month.getFullYear(), month.getMonth() + step, 1));
}

/**
 * Выбор дня кликом или клавишей: первый - начало, второй - конец.
 * @param {string} iso - день.
 */
function pick(iso: string): void {
  if (pendingStart.value) commit(pendingStart.value, iso);
  else {
    pendingStart.value = iso;
    hoverDay.value = iso;
  }
}

/**
 * Нажали на день: может быть началом протягивания или обычным кликом - решит отпускание.
 * @param {PointerEvent} event - нажатие.
 * @param {string} iso - день.
 */
function handlePointerDown(event: PointerEvent, iso: string): void {
  if (event.button !== 0) return; // только основная кнопка мыши
  event.preventDefault(); // без выделения текста при протягивании
  focusedDay.value = iso;
  dragStart.value = iso;
  hoverDay.value = iso;
  document.addEventListener('pointerup', handlePointerUp, { once: true });
}

/**
 * Отпустили: протянули на другой день - период готов; на том же дне - это клик.
 */
function handlePointerUp(): void {
  const start = dragStart.value;
  const end = hoverDay.value;
  dragStart.value = null;
  if (!start) return;
  if (end && end !== start) commit(start, end);
  else pick(start);
}

/**
 * Курсор или палец над сеткой: день под ним - для подсветки будущего периода.
 * Через elementFromPoint, а не pointerenter: при касании события достаются только первому дню.
 * @param {PointerEvent} event - движение.
 */
function handlePointerMove(event: PointerEvent): void {
  if (!dragStart.value && !pendingStart.value) return;
  const target = document.elementFromPoint(event.clientX, event.clientY);
  const iso = target instanceof HTMLElement ? target.dataset.day : undefined;
  if (iso) hoverDay.value = iso;
}

/**
 * Клавиатура в сетке дней.
 * @param {KeyboardEvent} event - нажатие.
 * @param {string} iso - день с фокусом.
 */
async function handleDayKeydown(event: KeyboardEvent, iso: string): Promise<void> {
  const day = parseIsoDate(iso);
  let next: Date | null = null;
  if (event.key in KEY_STEPS) {
    next = new Date(day.getFullYear(), day.getMonth(), day.getDate() + KEY_STEPS[event.key]);
  } else if (event.key in MONTH_KEYS) {
    next = new Date(day.getFullYear(), day.getMonth() + MONTH_KEYS[event.key], day.getDate());
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    pick(iso);
    return;
  }
  if (!next) return;

  event.preventDefault();
  const nextIso = toIsoDate(next);
  if (pendingStart.value) hoverDay.value = nextIso;
  await focusDay(nextIso);
}

/**
 * Перевести фокус на день, при необходимости показав его месяц.
 * @param {string} iso - день.
 */
async function focusDay(iso: string): Promise<void> {
  focusedDay.value = iso;
  viewMonth.value = startOfMonth(iso); // день другого месяца - показываем его месяц
  await nextTick();
  grid.value?.querySelector<HTMLElement>(`[data-day="${iso}"]`)?.focus();
}

/**
 * Клик мимо календаря - закрыть.
 * @param {PointerEvent} event - нажатие где-то на странице.
 */
function handleOutside(event: PointerEvent): void {
  if (root.value && !root.value.contains(event.target as Node)) close();
}

watch(isOpen, open => {
  if (open) document.addEventListener('pointerdown', handleOutside);
  else document.removeEventListener('pointerdown', handleOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleOutside);
  document.removeEventListener('pointerup', handlePointerUp);
});
</script>

<style lang="scss" module>
$day-size: 2.25rem;

.VDateRange {
  min-width: 0;
}

.root {
  position: relative;
}

.field {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  justify-content: space-between;
  text-align: left;
  cursor: pointer;

  @include control;

  &._empty .value {
    color: var(--base-500);
  }
}

.value {
  @include ellipsis;
}

// Значок календаря - рамка с «ушками», нарисованная CSS
.icon {
  position: relative;
  flex-shrink: 0;
  width: 1rem;
  height: 0.875rem;
  border: var(--focus-width) solid var(--base-500);
  border-radius: var(--radius-small);

  &::before {
    position: absolute;
    top: 0.125rem;
    right: 0;
    left: 0;
    height: var(--focus-width);
    content: '';
    background: var(--base-500);
  }
}

.popover {
  position: absolute;
  top: calc(100% + var(--space-1));
  left: 0;
  z-index: var(--z-dropdown);
  display: grid;
  gap: var(--space-2);
  width: max-content;
  max-width: calc(100vw - 2 * var(--space-4));
  padding: var(--space-3);
  background: var(--white);
  border: var(--border-width) solid var(--base-300);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.month {
  font-weight: 600;

  @include text(body);
}

.nav {
  width: $day-size;
  height: $day-size;
  color: var(--base-700);
  cursor: pointer;
  background: none;
  border: 0;
  border-radius: var(--radius-small);

  @include text(h3);

  &:hover {
    background: var(--base-100);
  }

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
  }
}

.weekdays,
.grid {
  display: grid;
  grid-template-columns: repeat(7, $day-size);
}

.weekdays {
  color: var(--base-500);
  text-align: center;

  @include text(caption);
}

.grid {
  touch-action: none;
  user-select: none;
}

.day {
  width: $day-size;
  height: $day-size;
  color: var(--base-900);
  font-variant-numeric: tabular-nums;
  cursor: pointer;
  background: none;
  border: 0;
  border-radius: var(--radius-small);

  @include text(small);

  &:hover {
    background: var(--base-100);
  }

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: calc(-1 * var(--focus-width));
  }

  &._outside,
  &._noData {
    color: var(--base-500);
  }

  &._inRange {
    background: var(--primary-100);
    border-radius: 0;
  }

  &._edge {
    color: var(--white);
    background: var(--primary-500);
    border-radius: var(--radius-small);
  }
}

.footer {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  justify-content: space-between;
  max-width: calc(7 * #{$day-size});
}

.tip {
  color: var(--base-700);

  @include text(caption);
}

.clear {
  flex-shrink: 0;
  padding: var(--space-1) var(--space-2);
  color: var(--primary-600);
  cursor: pointer;
  background: none;
  border: 0;
  border-radius: var(--radius-small);

  @include text(small);

  &:hover {
    background: var(--base-100);
  }

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
  }
}
</style>
