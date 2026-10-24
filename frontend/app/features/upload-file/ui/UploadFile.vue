<template>
  <div :class="$style.UploadFile">
    <VFileDrop
      :accept="FILE_ACCEPT"
      :hint="FILE_HINT"
      :loading="isUploadingOwnFile"
      :disabled="isBusy"
      @select="openFile"
    />

    <VAlert v-if="error" :variant="ALERT_VARIANTS.error">{{ error }}</VAlert>

    <section v-if="examples.length" :class="$style.examples" :aria-labelledby="examplesTitleId">
      <h3 :id="examplesTitleId" :class="$style.examplesTitle">Нет своего файла? Откройте пример</h3>
      <ul :class="$style.examplesList">
        <li v-for="example in examples" :key="example.name">
          <VButton
            :variant="BUTTON_VARIANTS.secondary"
            :loading="openingName === example.name"
            :disabled="isBusy"
            @click="openExample(example.name)"
          >
            {{ example.title }}
          </VButton>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * Загрузка выгрузки продаж: свой файл перетаскиванием или кнопкой, либо тестовый пример.
 * Формат и размер проверяются до отправки; ошибки сервера - понятным текстом.
 * После открытия файл попадает в сессию (entities/session).
 */
import { computed, onMounted, ref, useId } from 'vue';
import { fetchExamples } from '~/entities/session';
import type { ExampleInfo } from '~/shared/api';
import { ALERT_VARIANTS, BUTTON_VARIANTS, VAlert, VButton, VFileDrop } from '~/shared/ui';
import { FILE_ACCEPT, FILE_HINT } from '../lib/validate-file';
import { useOpenFile } from '../model/useOpenFile';

const { openingName, error, openFile, openExample } = useOpenFile();

const examples = ref<ExampleInfo[]>([]);
const examplesTitleId = useId();

// Пока открывается что-то одно - остальное неактивно: не запустить две загрузки сразу
const isBusy = computed(() => openingName.value !== null);
const exampleNames = computed(() => new Set(examples.value.map(example => example.name)));
const isUploadingOwnFile = computed(
  () => isBusy.value && !exampleNames.value.has(openingName.value as string),
);

onMounted(async () => {
  // Примеры - приятное дополнение: не загрузились - просто не показываем блок
  try {
    examples.value = await fetchExamples();
  } catch {
    examples.value = [];
  }
});
</script>

<style lang="scss" module>
.UploadFile {
  display: grid;
  gap: var(--space-4);
}

.examples {
  display: grid;
  gap: var(--space-3);
}

.examplesTitle {
  color: var(--base-700);

  @include text(small);

  font-weight: 600;
}

.examplesList {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
