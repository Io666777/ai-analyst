/** Вид сообщения: сведения, успех, предупреждение, ошибка. */
export const ALERT_VARIANTS = {
  info: 'info',
  success: 'success',
  warning: 'warning',
  error: 'error',
} as const;

export type AlertVariant = (typeof ALERT_VARIANTS)[keyof typeof ALERT_VARIANTS];
