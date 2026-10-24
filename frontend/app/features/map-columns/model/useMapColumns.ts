// Разметка колонок: роли, проверка, отправка на сервер
import type { ComputedRef, Ref } from 'vue';
import { computed, onMounted, ref } from 'vue';
import { COLUMN_ROLES } from '~/entities/column-role';
import { useOptions, useSession } from '~/entities/session';
import { toApiError } from '~/shared/api';
import type { SelectOption } from '~/shared/ui';
import { hasMappingErrors, type MappingErrors, validateMapping } from '../lib/validate-mapping';

const NO_ERRORS: MappingErrors = { byColumn: {}, general: [] };

export interface UseMapColumns {
  /** Колонка → выбранная роль. */
  mapping: Ref<Record<string, string>>;
  /** Варианты ролей для списков. */
  roleOptions: ComputedRef<SelectOption[]>;
  /** Ошибки - показываются после первой попытки отправить. */
  errors: ComputedRef<MappingErrors>;
  /** Ошибка сервера или загрузки справочника. */
  requestError: Ref<string | null>;
  isLoadingOptions: Ref<boolean>;
  isSaving: Ref<boolean>;
  /** Отправить разметку. true - готово, данные подготовлены. */
  submit: () => Promise<boolean>;
}

/**
 * Разметка колонок открытого файла.
 * Начальные роли: прежняя разметка, затем готовая (у примеров), иначе «не нужна».
 * @returns {UseMapColumns} состояние и действия.
 */
export function useMapColumns(): UseMapColumns {
  const session = useSession();
  const { options, loadOptions } = useOptions();

  const { columns, mapping: applied, suggestedMapping } = session.state.value;
  const mapping = ref<Record<string, string>>(
    Object.fromEntries(
      columns.map(column => [
        column.name,
        applied?.[column.name] ?? suggestedMapping?.[column.name] ?? COLUMN_ROLES.ignore,
      ]),
    ),
  );

  const isSubmitted = ref(false);
  const isLoadingOptions = ref(false);
  const isSaving = ref(false);
  const requestError = ref<string | null>(null);

  const roleOptions = computed<SelectOption[]>(() =>
    (options.value?.roles ?? []).map(role => ({ value: role.value, label: role.label })),
  );

  // До первой попытки отправить - без красного: человек ещё не закончил
  const errors = computed(() => (isSubmitted.value ? validateMapping(mapping.value) : NO_ERRORS));

  onMounted(async () => {
    isLoadingOptions.value = true;
    try {
      await loadOptions();
    } catch (error) {
      requestError.value = toApiError(error).message;
    } finally {
      isLoadingOptions.value = false;
    }
  });

  /**
   * Проверка → отправка → отчёт о подготовке в сессии.
   * @returns {Promise<boolean>} true - разметка принята сервером.
   */
  async function submit(): Promise<boolean> {
    isSubmitted.value = true;
    requestError.value = null;
    if (hasMappingErrors(validateMapping(mapping.value))) return false;

    isSaving.value = true;
    try {
      await session.applyMapping(mapping.value);
      return true;
    } catch (error) {
      requestError.value = toApiError(error).message;
      return false;
    } finally {
      isSaving.value = false;
    }
  }

  return { mapping, roleOptions, errors, requestError, isLoadingOptions, isSaving, submit };
}
