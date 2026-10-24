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

    <VCard v-if="!session.isOpened.value" title="Откройте выгрузку продаж">
      <UploadFile />
      <p :class="$style.privacy">
        Файл обрабатывается в памяти сервера и никуда не сохраняется. Данные удаляются
        через 30 минут без работы или сразу - по кнопке «Удалить мои данные».
      </p>
    </VCard>

    <VCard v-else :title="session.state.value.fileName ?? undefined">
      <template #actions>
        <VButton
          :variant="BUTTON_VARIANTS.ghost"
          :size="BUTTON_SIZES.small"
          :loading="isForgetting"
          @click="handleForget"
        >
          Удалить мои данные
        </VButton>
      </template>

      <p :class="$style.summary">
        {{ pluralize(session.state.value.rows, ROW_FORMS) }},
        {{ pluralize(session.state.value.columns.length, COLUMN_FORMS) }}
      </p>
      <SessionColumns :columns="session.state.value.columns" />
      <VAlert v-if="forgetError" :variant="ALERT_VARIANTS.error">{{ forgetError }}</VAlert>
      <VAlert>
        Следующий шаг - разметка колонок: укажите, где дата, товар и сумма.
      </VAlert>
    </VCard>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { SessionColumns, useSession } from '~/entities/session';
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

const isForgetting = ref(false);
const forgetError = ref<string | null>(null);

/** «Удалить мои данные»: на сервере и в браузере - и снова экран загрузки. */
async function handleForget(): Promise<void> {
  forgetError.value = null;
  isForgetting.value = true;
  try {
    await session.forget();
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

.privacy,
.summary {
  color: var(--base-500);

  @include text(small);
}
</style>
