// Настройки анализа: служебные строки, валюта, страна праздников
import type { ComputedRef, Ref } from 'vue';
import { computed, onMounted, ref, watch } from 'vue';
import { useOptions, useSession } from '~/entities/session';
import { type SettingsApplied, toApiError } from '~/shared/api';
import type { SelectOption } from '~/shared/ui';
import { validateCurrency } from '../lib/validate-settings';

export interface UseChangeSettings {
  /** Отмеченные служебные строки - их не учитывать. */
  exclude: Ref<string[]>;
  currency: Ref<string>;
  country: Ref<string>;
  /** Что можно исключить: найденное сервером и уже исключённое раньше. */
  candidates: ComputedRef<string[]>;
  countryOptions: ComputedRef<SelectOption[]>;
  /** Ошибка валюты - показывается после первой попытки применить. */
  currencyError: ComputedRef<string | undefined>;
  /** Ответ сервера на последнее применение: сколько строк убрано. */
  applied: Ref<SettingsApplied | null>;
  requestError: Ref<string | null>;
  isSaving: Ref<boolean>;
  /** Применить настройки. true - сервер принял. */
  submit: () => Promise<boolean>;
}

/**
 * Настройки анализа размеченного файла. Начальные значения - из сессии.
 * @returns {UseChangeSettings} состояние и действия.
 */
export function useChangeSettings(): UseChangeSettings {
  const session = useSession();
  const { options, loadOptions } = useOptions();

  const { settings } = session.state.value;
  const exclude = ref<string[]>([...settings.exclude]);
  const currency = ref(settings.currency);
  const country = ref(settings.country);

  const isSubmitted = ref(false);
  const isSaving = ref(false);
  const applied = ref<SettingsApplied | null>(null);
  const requestError = ref<string | null>(null);

  const candidates = computed(() => {
    const suggested = session.state.value.prepared?.suggested_exclusions ?? [];
    return [...new Set([...suggested, ...session.state.value.settings.exclude])].sort();
  });

  const countryOptions = computed<SelectOption[]>(() =>
    (options.value?.countries ?? []).map(item => ({ value: item.value, label: item.label })),
  );

  const currencyError = computed(() =>
    isSubmitted.value ? validateCurrency(currency.value) : undefined,
  );

  // Поменяли что-то после «Применить» - старое «применено» уже неправда
  watch([exclude, currency, country], () => {
    applied.value = null;
  });

  onMounted(async () => {
    try {
      await loadOptions();
    } catch (error) {
      requestError.value = toApiError(error).message;
    }
  });

  /**
   * Проверка → отправка → новые настройки в сессии.
   * @returns {Promise<boolean>} true - настройки применены.
   */
  async function submit(): Promise<boolean> {
    isSubmitted.value = true;
    requestError.value = null;
    if (validateCurrency(currency.value)) return false;

    isSaving.value = true;
    try {
      applied.value = await session.applySettings({
        exclude: exclude.value,
        currency: currency.value.trim(),
        country: country.value,
      });
      return true;
    } catch (error) {
      requestError.value = toApiError(error).message;
      return false;
    } finally {
      isSaving.value = false;
    }
  }

  return {
    exclude,
    currency,
    country,
    candidates,
    countryOptions,
    currencyError,
    applied,
    requestError,
    isSaving,
    submit,
  };
}
