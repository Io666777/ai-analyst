<template>
  <div :class="$style.UploadFile">
    <VFileDrop
      :accept="FILE_ACCEPT"
      :hint="FILE_HINT"
      :loading="isOpening"
      :disabled="isOpening"
      @select="openFile"
    />

    <VAlert v-if="error" :variant="ALERT_VARIANTS.error">{{ error }}</VAlert>
  </div>
</template>

<script setup lang="ts">
/**
 * Загрузка выгрузки продаж: перетаскиванием или кнопкой.
 * Формат и размер проверяются до отправки; ошибки сервера - понятным текстом.
 * После открытия файл попадает в сессию (entities/session).
 */
import { ALERT_VARIANTS, VAlert, VFileDrop } from '~/shared/ui';
import { FILE_ACCEPT, FILE_HINT } from '../lib/validate-file';
import { useOpenFile } from '../model/useOpenFile';

const { isOpening, error, openFile } = useOpenFile();
</script>

<style lang="scss" module>
.UploadFile {
  display: grid;
  gap: var(--space-4);
}
</style>
