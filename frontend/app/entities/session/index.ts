// Публичный вход слайса entities/session: снаружи импортируем только отсюда
export { fetchExamples, fetchOptions } from './api/session-api';
export {
  type SessionSettings,
  type SessionState,
  type UseSession,
  useSession,
} from './model/useSession';
