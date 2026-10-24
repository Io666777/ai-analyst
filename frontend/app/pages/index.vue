<template>
  <div :class="$style.IndexPage">
    <header :class="$style.header">
      <h1 :class="$style.title">AI-аналитик для малого бизнеса</h1>
      <p :class="$style.lead">
        Загрузите выгрузку продаж - программа покажет, как идут дела, что продаётся лучше всего
        и сколько ждать в следующие недели.
      </p>
    </header>

    <VAlert
      v-if="session.state.value.expired"
      :variant="ALERT_VARIANTS.warning"
      title="Сессия устарела - загрузите файл заново"
    >
      Данные удалены с сервера после 30 минут без работы: так они не хранятся дольше нужного.
    </VAlert>

    <!-- 1. Файл ещё не открыт -->
    <VCard v-if="!session.isOpened.value" title="Откройте выгрузку продаж">
      <UploadFile />
      <p :class="$style.note">
        Файл обрабатывается в памяти сервера и никуда не сохраняется. Данные удаляются
        через 30 минут без работы или сразу - по кнопке «Удалить мои данные».
      </p>
    </VCard>

    <!-- 2-3. Файл открыт: разметка или отчёт о подготовке -->
    <VCard v-else :title="session.state.value.fileName ?? undefined">
      <template #actions>
        <VButton
          v-if="session.isPrepared.value && !isEditingMapping"
          :variant="BUTTON_VARIANTS.ghost"
          :size="BUTTON_SIZES.small"
          @click="isEditingMapping = true"
        >
          Изменить разметку
        </VButton>
        <VButton
          :variant="BUTTON_VARIANTS.ghost"
          :size="BUTTON_SIZES.small"
          :loading="isForgetting"
          @click="handleForget"
        >
          Удалить мои данные
        </VButton>
      </template>

      <p :class="$style.note">
        {{ pluralize(session.state.value.rows, ROW_FORMS) }},
        {{ pluralize(session.state.value.columns.length, COLUMN_FORMS) }}
      </p>

      <MapColumns
        v-if="!session.isPrepared.value || isEditingMapping"
        :cancelable="isEditingMapping"
        @done="isEditingMapping = false"
        @cancel="isEditingMapping = false"
      />

      <template v-else-if="session.state.value.prepared">
        <PreparationReport :prepared="session.state.value.prepared" :field-labels="fieldLabels" />
        <VAlert :variant="ALERT_VARIANTS.success" title="Данные готовы к анализу">
          Проверьте настройки ниже - и переходите к разделам: обзор, топ, товар, сравнение
          периодов, прогноз.
        </VAlert>
      </template>

      <VAlert v-if="forgetError" :variant="ALERT_VARIANTS.error">{{ forgetError }}</VAlert>
    </VCard>

    <!-- 4. Настройки анализа: после разметки, пока её не меняют -->
    <VCard
      v-if="session.isPrepared.value && !isEditingMapping"
      title="Настройки анализа"
    >
      <ChangeSettings />
    </VCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { PreparationReport, useOptions, useSession } from '~/entities/session';
import { ChangeSettings } from '~/features/change-settings';
import { MapColumns } from '~/features/map-columns';
import { UploadFile } from '~/features/upload-file';
import { toApiError } from '~/shared/api';
import { pluralize, type WordForms } from '~/shared/lib';
import {
  ALERT_VARIANTS,
  BUTTON_SIZES,
  BUTTON_VARIANTS,
  VAlert,
  VButton,
  VCard,
} from '~/shared/ui';

const ROW_FORMS: WordForms = { one: 'строка', few: 'строки', many: 'строк' };
const COLUMN_FORMS: WordForms = { one: 'колонка', few: 'колонки', many: 'колонок' };

const session = useSession();
const { options, loadOptions } = useOptions();

const isEditingMapping = ref(false);
const isForgetting = ref(false);
const forgetError = ref<string | null>(null);

// Подписи полей в отчёте - из справочника ролей: amount → "сумма, деньги"
const fieldLabels = computed<Record<string, string>>(() =>
  Object.fromEntries((options.value?.roles ?? []).map(role => [role.value, role.label])),
);

onMounted(async () => {
  // Справочник нужен для подписей в отчёте; не загрузился - покажем названия полей как есть
  try {
    await loadOptions();
  } catch {
    // подписи - не главное: отчёт виден и без них
  }
});

/** «Удалить мои данные»: на сервере и в браузере - и снова экран загрузки. */
async function handleForget(): Promise<void> {
  forgetError.value = null;
  isForgetting.value = true;
  try {
    await session.forget();
    isEditingMapping.value = false;
  } catch (error) {
    forgetError.value = toApiError(error).message;
  } finally {
    isForgetting.value = false;
  }
}
</script>

<style lang="scss" module>
.IndexPage {
  display: grid;
  gap: var(--space-5);
}

.header {
  display: grid;
  gap: var(--space-2);
}

.title {
  @include text(h1);
}

.lead {
  max-width: 45rem;
  color: var(--base-700);
}

.note {
  color: var(--base-500);

  @include text(small);
}
</style>
