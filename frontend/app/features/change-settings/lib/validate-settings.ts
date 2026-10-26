// Проверка настроек до отправки - те же ограничения, что на сервере (SettingsRequest)

export const CURRENCY_MAX_LENGTH = 10;

export const SETTINGS_ERRORS = {
  noCurrency: 'Укажите валюту - она подписывает суммы в отчётах',
  longCurrency: `Валюта - не длиннее ${CURRENCY_MAX_LENGTH} символов: «р.», «BYN», «$»`,
} as const;

/**
 * Проверяет валюту.
 * @param {string} currency - как подписывать суммы.
 * @returns {string | undefined} текст ошибки; undefined - подходит.
 */
export function validateCurrency(currency: string): string | undefined {
  const value = currency.trim();
  if (!value) return SETTINGS_ERRORS.noCurrency;
  if (value.length > CURRENCY_MAX_LENGTH) return SETTINGS_ERRORS.longCurrency;
  return undefined;
}
