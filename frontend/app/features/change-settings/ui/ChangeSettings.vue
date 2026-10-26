<template>
  <form :class="$style.ChangeSettings" novalidate @submit.prevent="submit">
    <fieldset :class="$style.group">
      <legend :class="$style.legend">Служебные строки</legend>
      <template v-if="candidates.length">
        <p :class="$style.note">
          Похоже, это не продажи: доставка, комиссии, скидки. Отмеченное не попадёт в анализ.
        </p>
        <div :class="$style.checks">
          <VCheckbox
            v-for="name in candidates"
            :key="name"
            :model-value="exclude.includes(name)"
            :label="name"
            @update:model-value="toggle(name, $event)"
          />
        </div>
      </template>
      <p v-else :class="$style.note">Служебных строк (доставка, комиссии) не нашлось.</p>
    </fieldset>

    <div :class="$style.fields">
      <VInput
        v-model="currency"
        label="Валюта"
        hint="Как подписывать суммы: «р.», «BYN», «$»"
        :error="currencyError"
        required
      />
      <VSelect
        v-model="country"
        label="Учитывать праздники"
        hint="В праздники продажи идут иначе - прогноз это учтёт"
        :options="countryOptions"
      />
    </div>

    <VAlert v-if="requestError" :variant="ALERT_VARIANTS.error">{{ requestError }}</VAlert>
    <VAlert v-else-if="applied" :variant="ALERT_VARIANTS.success" title="Настройки применены">
      {{ appliedText }}
    </VAlert>

    <div :class="$style.actions">
      <VButton type="submit" :loading="isSaving">Применить</VButton>
    </div>
  </form>
</template>

<script setup lang="ts">
/**
 * Настройки анализа: какие служебные строки не учитывать, валюта, страна праздников.
 * Можно не трогать - сервер уже работает с настройками по умолчанию.
 */
import { computed } from 'vue';
import { formatMoney, pluralize, type WordForms } from '~/shared/lib';
import { ALERT_VARIANTS, VAlert, VButton, VCheckbox, VInput, VSelect } from '~/shared/ui';
import { useChangeSettings } from '../model/useChangeSettings';

const ROW_FORMS: WordForms = { one: 'строка', few: 'строки', many: 'строк' };

const {
  exclude,
  currency,
  country,
  candidates,
  countryOptions,
  currencyError,
  applied,
  requestError,
  isSaving,
  submit,
} = useChangeSettings();

const appliedText = computed(() => {
  if (!applied.value?.excluded_rows) return 'Все строки учитываются в анализе.';
  const { excluded_rows: rows, excluded_amount: amount, currency: unit } = applied.value;
  // Без точки в конце: валюта «р.» сама кончается точкой - вышло бы «р..»
  return `Не учитывается ${pluralize(rows, ROW_FORMS)} на ${formatMoney(amount, unit)}`;
});

/**
 * Отметить или снять служебную строку.
 * @param {string} name - товар.
 * @param {boolean} checked - отмечен ли флажок.
 */
function toggle(name: string, checked: boolean): void {
  exclude.value = checked
    ? [...exclude.value, name]
    : exclude.value.filter(item => item !== name);
}
</script>

<style lang="scss" module>
.ChangeSettings {
  display: grid;
  gap: var(--space-4);
}

.group {
  display: grid;
  gap: var(--space-2);
  min-width: 0;
  padding: 0;
  margin: 0;
  border: 0;
}

.legend {
  padding: 0;
  margin-bottom: var(--space-2);
  color: var(--base-900);

  @include text(h3);
}

.note {
  color: var(--base-700);

  @include text(small);
}

.checks {
  display: grid;
  gap: var(--space-1);
}

.fields {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: var(--space-4);
  align-items: start;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
