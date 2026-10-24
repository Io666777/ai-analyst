// Публичный вход слайса entities/session: снаружи импортируем только отсюда
export { fetchExamples, fetchOptions } from './api/session-api';
export { type UseOptions, useOptions } from './model/useOptions';
export {
  type SessionSettings,
  type SessionState,
  type UseSession,
  useSession,
} from './model/useSession';
export { default as PreparationReport } from './ui/PreparationReport.vue';
export { default as SessionColumns } from './ui/SessionColumns.vue';
