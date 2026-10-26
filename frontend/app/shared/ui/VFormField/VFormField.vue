<template>
  <div :class="$style.VFormField">
    <label :for="fieldId" :class="$style.label">
      {{ label }}
      <span v-if="required" :class="$style.required" aria-hidden="true">*</span>
    </label>

    <slot :id="fieldId" :described-by="describedBy" :invalid="Boolean(error)" />

    <p v-if="error" :id="messageId" :class="$style.error" role="alert">{{ error }}</p>
    <p v-else-if="warning" :id="messageId" :class="$style.warning">
      <span :class="$style.mark" aria-hidden="true">!</span>{{ warning }}
    </p>
    <p v-else-if="hint" :id="messageId" :class="$style.hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
/**
 * Обвязка поля формы: подпись, звёздочка «обязательно», подсказка или ошибка.
 * Само поле вставляется в слот и получает id и атрибуты для экранного диктора.
 * Общая для VInput и VSelect - чтобы не повторять одно и то же в каждом поле.
 *
 * @example
 * <VFormField v-slot="{ id, describedBy, invalid }" label="Страна" :error="error">
 *   <select :id="id" :aria-describedby="describedBy" :aria-invalid="invalid" />
 * </VFormField>
 */
// shared не зависит от Nuxt: всё из vue - явно (и Storybook собирает компонент без Nuxt)
import { computed, useId } from 'vue';

const props = withDefaults(
  defineProps<{
    /** Подпись над полем - обязательна: placeholder её не заменяет. */
    label: string;
    /** Подсказка под полем. */
    hint?: string;
    /** Текст ошибки - показывается вместо подсказки. */
    error?: string;
    /** Обратить внимание, но это не ошибка: «проверьте, программа не уверена». Вместо подсказки. */
    warning?: string;
    /** Поле обязательно - звёздочка у подписи. */
    required?: boolean;
  }>(),
  {
    hint: undefined,
    error: undefined,
    warning: undefined,
    required: false,
  },
);

defineSlots<{
  /** Само поле. id - связать с подписью, describedBy и invalid - для экранного диктора. */
  default: (props: { id: string; describedBy: string | undefined; invalid: boolean }) => unknown;
}>();

// Свой id у каждого поля: клик по подписи ставит курсор в поле, диктор читает подсказку
const fieldId = useId();
const messageId = `${fieldId}-message`;

const describedBy = computed(() =>
  props.error || props.warning || props.hint ? messageId : undefined,
);
</script>

<style lang="scss" module>
.VFormField {
  display: grid;
  align-content: start; // без подсказки поле не "сползает" вниз в ряду с соседями
  gap: var(--space-1);
}

.label {
  color: var(--base-700);
  user-select: none;

  @include text(small);
}

.required {
  color: var(--error-500);
}

.hint {
  color: var(--base-500);

  @include text(caption);
}

.error {
  color: var(--error-500);

  @include text(caption);
}

// Текст тёмный (контраст), а внимание привлекает жёлтый кружок с «!»
.warning {
  display: flex;
  gap: var(--space-1);
  align-items: baseline;
  color: var(--base-900);

  @include text(caption);
}

.mark {
  display: inline-grid;
  flex-shrink: 0;
  place-items: center;
  width: 1rem;
  height: 1rem;
  color: var(--white);
  background: var(--warning-500);
  border-radius: 50%;
  font-weight: 700;
}
</style>
