// Открыть файл или пример: проверка до отправки, загрузка, понятная ошибка, состояние "загружаю"
import type { Ref } from 'vue';
import { ref } from 'vue';
import { useSession } from '~/entities/session';
import { toApiError } from '~/shared/api';
import { validateFile } from '../lib/validate-file';

export interface UseOpenFile {
  /** Что сейчас открывается: имя файла или примера; null - ничего. */
  openingName: Ref<string | null>;
  /** Текст ошибки для показа; null - ошибки нет. */
  error: Ref<string | null>;
  openFile: (file: File) => Promise<void>;
  openExample: (name: string) => Promise<void>;
}

/**
 * Открытие своего файла и тестового примера - одинаковое поведение для обоих.
 * @returns {UseOpenFile} состояние и действия.
 */
export function useOpenFile(): UseOpenFile {
  const session = useSession();
  const openingName = ref<string | null>(null);
  const error = ref<string | null>(null);

  /**
   * Общая часть: "загружаю", запрос, понятная ошибка.
   * @param {string} name - что открываем - для состояния "загружаю".
   * @param {() => Promise<unknown>} open - сам запрос.
   */
  async function run(name: string, open: () => Promise<unknown>): Promise<void> {
    error.value = null;
    openingName.value = name;
    try {
      await open();
    } catch (requestError) {
      error.value = toApiError(requestError).message;
    } finally {
      openingName.value = null;
    }
  }

  /**
   * Свой файл: сначала проверка формата и размера - без похода на сервер.
   * @param {File} file - выбранный файл.
   */
  async function openFile(file: File): Promise<void> {
    const invalid = validateFile(file);
    if (invalid) {
      error.value = invalid;
      return;
    }
    await run(file.name, () => session.openFile(file));
  }

  /**
   * Тестовый пример.
   * @param {string} name - имя файла примера.
   */
  async function openExample(name: string): Promise<void> {
    await run(name, () => session.openExample(name));
  }

  return { openingName, error, openFile, openExample };
}
