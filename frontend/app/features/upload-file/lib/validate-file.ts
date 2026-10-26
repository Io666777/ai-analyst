import { ALLOWED_FILE_EXTENSIONS, MAX_UPLOAD_MB } from '~/shared/config';

const BYTES_IN_MB = 1024 * 1024;

/** Тексты ошибок - те же, что у сервера: человек видит одно и то же, где бы ни поймали. */
export const FILE_ERRORS = {
  format: 'Нужен файл Excel (.xlsx, .xls) или CSV',
  size: `Файл больше ${MAX_UPLOAD_MB} МБ`,
  empty: 'Файл пустой',
} as const;

/** Для окна выбора файла: ".csv,.xlsx,.xls". */
export const FILE_ACCEPT = ALLOWED_FILE_EXTENSIONS.join(',');

/** Подсказка под полем. */
export const FILE_HINT = `Excel (.xlsx, .xls) или CSV, до ${MAX_UPLOAD_MB} МБ`;

/**
 * Расширение файла в нижнем регистре: "Продажи.XLSX" → ".xlsx".
 * @param {string} name - имя файла.
 * @returns {string} расширение с точкой или пустая строка.
 */
function extensionOf(name: string): string {
  const dot = name.lastIndexOf('.');
  return dot === -1 ? '' : name.slice(dot).toLowerCase();
}

/**
 * Проверка файла до отправки: формат, размер, не пустой.
 * Сервер проверит то же самое, но так ошибка видна сразу, без загрузки по сети.
 * @param {File} file - выбранный файл.
 * @returns {string | null} текст ошибки или null - файл подходит.
 */
export function validateFile(file: File): string | null {
  const extensions: readonly string[] = ALLOWED_FILE_EXTENSIONS;
  if (!extensions.includes(extensionOf(file.name))) return FILE_ERRORS.format;
  if (file.size === 0) return FILE_ERRORS.empty;
  if (file.size > MAX_UPLOAD_MB * BYTES_IN_MB) return FILE_ERRORS.size;
  return null;
}
