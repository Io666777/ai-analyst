// Открыть файл: проверка до отправки, загрузка, понятная ошибка, состояние "загружаю"
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useSession } from '~/entities/session';
import { toApiError } from '~/shared/api';
import { validateFile } from '../lib/validate-file';

export interface UseOpenFile {
  /** Файл загружается. */
  isOpening: Ref<boolean>;
  /** Текст ошибки для показа; null - ошибки нет. */
  error: Ref<string | null>;
  openFile: (file: File) => Promise<void>;
}

/**
 * Открытие своего файла.
 * @returns {UseOpenFile} состояние и действие.
 */
export function useOpenFile(): UseOpenFile {
  const session = useSession();
  const isOpening = ref(false);
  const error = ref<string | null>(null);

  /**
   * Свой файл: сначала проверка формата и размера - без похода на сервер.
   * @param {File} file - выбранный файл.
   */
  async function openFile(file: File): Promise<void> {
    error.value = validateFile(file);
    if (error.value) return;

    isOpening.value = true;
    try {
      await session.openFile(file);
    } catch (requestError) {
      error.value = toApiError(requestError).message;
    } finally {
      isOpening.value = false;
    }
  }

  return { isOpening, error, openFile };
}
