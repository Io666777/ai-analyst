// Запросы сессии: открыть файл или пример, справочник, разметка, настройки, удаление
import {
  api,
  type ExampleInfo,
  type FileOpened,
  type Options,
  type PreparedData,
  type SettingsApplied,
  type SettingsRequest,
} from '~/shared/api';
import { API_ENDPOINTS, exampleEndpoint } from '~/shared/config';

/**
 * Загрузить свой файл - начать новую сессию.
 * @param {File} file - Excel или CSV.
 * @returns {Promise<FileOpened>} номер сессии и колонки для разметки.
 */
export function uploadFile(file: File): Promise<FileOpened> {
  return api.upload<FileOpened>(API_ENDPOINTS.files, file);
}

/**
 * Список тестовых примеров.
 * @returns {Promise<ExampleInfo[]>} примеры: имя файла и описание.
 */
export function fetchExamples(): Promise<ExampleInfo[]> {
  return api.get<ExampleInfo[]>(API_ENDPOINTS.examples);
}

/**
 * Открыть тестовый пример - начать новую сессию с готовой разметкой.
 * @param {string} name - имя файла примера.
 * @returns {Promise<FileOpened>} номер сессии, колонки и готовая разметка.
 */
export function openExampleFile(name: string): Promise<FileOpened> {
  return api.post<FileOpened>(exampleEndpoint(name));
}

/**
 * Справочник: роли колонок и страны праздников.
 * @returns {Promise<Options>} варианты для выпадающих списков.
 */
export function fetchOptions(): Promise<Options> {
  return api.get<Options>(API_ENDPOINTS.options);
}

/**
 * Разметить колонки - сервер чистит данные и строит события.
 * @param {Record<string, string>} mapping - колонка файла -> роль.
 * @returns {Promise<PreparedData>} отчёт о подготовке.
 */
export function putMapping(mapping: Record<string, string>): Promise<PreparedData> {
  return api.put<PreparedData>(API_ENDPOINTS.mapping, { mapping });
}

/**
 * Настройки анализа: служебные строки, валюта, страна праздников.
 * @param {SettingsRequest} settings - настройки.
 * @returns {Promise<SettingsApplied>} применённые настройки и сколько строк исключено.
 */
export function putSettings(settings: SettingsRequest): Promise<SettingsApplied> {
  return api.put<SettingsApplied>(API_ENDPOINTS.settings, { ...settings });
}

/**
 * Удалить данные сессии с сервера.
 * @returns {Promise<void>} ничего.
 */
export function deleteSession(): Promise<void> {
  return api.delete(API_ENDPOINTS.session);
}
