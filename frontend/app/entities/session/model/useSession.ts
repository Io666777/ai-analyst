// Сессия - память фронта о текущей работе с файлом: номер на сервере, колонки, разметка,
// отчёт подготовки, настройки. Общая для всех страниц (useState).
// Живёт только в памяти вкладки: обновил или закрыл страницу - забыто,
// а данные на сервере сами удалятся через 30 минут
import type { ComputedRef, DeepReadonly, Ref } from 'vue';
import { computed, readonly } from 'vue';
import { useState } from '#imports';
import type {
  ColumnPreview,
  FileOpened,
  PreparedData,
  SettingsApplied,
  SettingsRequest,
} from '~/shared/api';
import { ApiError } from '~/shared/api';
import { DEFAULT_COUNTRY, DEFAULT_CURRENCY } from '~/shared/config';
import {
  deleteSession,
  openExampleFile,
  putMapping,
  putSettings,
  uploadFile,
} from '../api/session-api';

const SESSION_STATE_KEY = 'session';

export interface SessionSettings {
  exclude: string[];
  currency: string;
  country: string;
}

export interface SessionState {
  /** Номер сессии на сервере; null - файл ещё не открыт. */
  id: string | null;
  fileName: string | null;
  rows: number;
  columns: ColumnPreview[];
  /** Готовая разметка - есть только у тестовых примеров. */
  suggestedMapping: Record<string, string> | null;
  /** Применённая разметка. */
  mapping: Record<string, string> | null;
  /** Отчёт подготовки; null - колонки ещё не размечены. */
  prepared: PreparedData | null;
  settings: SessionSettings;
  /** Сессия устарела на сервере - показать «загрузите файл заново». */
  expired: boolean;
}

/**
 * Пустая сессия: файл не открыт.
 * @returns {SessionState} начальное состояние.
 */
function emptySession(): SessionState {
  return {
    id: null,
    fileName: null,
    rows: 0,
    columns: [],
    suggestedMapping: null,
    mapping: null,
    prepared: null,
    settings: { exclude: [], currency: DEFAULT_CURRENCY, country: DEFAULT_COUNTRY },
    expired: false,
  };
}

export interface UseSession {
  /** Состояние - только для чтения: менять через действия ниже. Читать: state.value.fileName */
  state: Readonly<Ref<DeepReadonly<SessionState>>>;
  /** Файл открыт. */
  isOpened: ComputedRef<boolean>;
  /** Колонки размечены - можно смотреть разделы анализа. */
  isPrepared: ComputedRef<boolean>;
  openFile: (file: File) => Promise<FileOpened>;
  openExample: (name: string) => Promise<FileOpened>;
  applyMapping: (mapping: Record<string, string>) => Promise<PreparedData>;
  applySettings: (settings: SettingsRequest) => Promise<SettingsApplied>;
  forget: () => Promise<void>;
  expire: () => void;
}

/**
 * Сессия: состояние и действия с ним.
 * @returns {UseSession} состояние только для чтения и действия.
 */
export function useSession(): UseSession {
  const state = useState<SessionState>(SESSION_STATE_KEY, emptySession);

  /**
   * Новая сессия: запоминаем, что открыли, а всё прежнее забываем.
   * @param {FileOpened} opened - ответ сервера на загрузку файла или примера.
   * @returns {FileOpened} тот же ответ - для цепочки.
   */
  function start(opened: FileOpened): FileOpened {
    state.value = {
      ...emptySession(),
      id: opened.session_id,
      fileName: opened.file_name,
      rows: opened.rows,
      columns: opened.columns,
      suggestedMapping: opened.mapping ?? null,
    };
    return opened;
  }

  /**
   * Открыть свой файл.
   * @param {File} file - Excel или CSV.
   * @returns {Promise<FileOpened>} колонки для разметки.
   */
  async function openFile(file: File): Promise<FileOpened> {
    return start(await uploadFile(file));
  }

  /**
   * Открыть тестовый пример.
   * @param {string} name - имя файла примера.
   * @returns {Promise<FileOpened>} колонки и готовая разметка.
   */
  async function openExample(name: string): Promise<FileOpened> {
    return start(await openExampleFile(name));
  }

  /**
   * Разметить колонки. Сервер сбрасывает исключения - сбрасываем и у себя.
   * @param {Record<string, string>} mapping - колонка -> роль.
   * @returns {Promise<PreparedData>} отчёт о подготовке.
   */
  async function applyMapping(mapping: Record<string, string>): Promise<PreparedData> {
    const prepared = await putMapping(mapping);
    state.value.mapping = { ...mapping };
    state.value.prepared = prepared;
    state.value.settings.exclude = [];
    return prepared;
  }

  /**
   * Применить настройки анализа.
   * @param {SettingsRequest} settings - исключения, валюта, страна.
   * @returns {Promise<SettingsApplied>} применённые настройки.
   */
  async function applySettings(settings: SettingsRequest): Promise<SettingsApplied> {
    const applied = await putSettings(settings);
    state.value.settings = {
      exclude: [...applied.exclude],
      currency: applied.currency,
      country: applied.country,
    };
    return applied;
  }

  /**
   * «Удалить мои данные»: на сервере и у себя. Сессия уже устарела - всё равно забываем.
   * @returns {Promise<void>} ничего.
   */
  async function forget(): Promise<void> {
    try {
      await deleteSession();
    } catch (error) {
      if (!(error instanceof ApiError && error.isSessionExpired)) throw error;
    }
    state.value = emptySession();
  }

  /** Сессия устарела на сервере: забываем и помечаем - главная покажет сообщение. */
  function expire(): void {
    state.value = { ...emptySession(), expired: true };
  }

  return {
    // Сама ссылка, а не state.value: при новом файле объект состояния заменяется целиком,
    // и защищённая копия старого объекта показывала бы устаревшие данные
    state: readonly(state),
    isOpened: computed(() => state.value.id !== null),
    isPrepared: computed(() => state.value.prepared !== null),
    openFile,
    openExample,
    applyMapping,
    applySettings,
    forget,
    expire,
  };
}
