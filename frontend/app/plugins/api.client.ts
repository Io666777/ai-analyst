// Слой app: при запуске настраиваем клиент API - откуда брать адрес сервера и номер сессии,
// и что делать, когда сервер сообщил «сессия устарела»: забыть сессию и вернуть на главную,
// где пользователь увидит «загрузите файл заново"
import { defineNuxtPlugin, navigateTo, useRuntimeConfig } from '#imports';
import { useSession } from '~/entities/session';
import { api, configureApiClient } from '~/shared/api';
import { API_ENDPOINTS, ROUTES } from '~/shared/config';

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig();
  const session = useSession();

  configureApiClient({
    baseUrl: config.public.apiUrl,
    getSessionId: () => session.state.value.id,
    onSessionExpired: () => {
      session.expire();
      navigateTo(ROUTES.home);
    },
  });

  // Бесплатный сервер Render засыпает без запросов и просыпается до минуты. Будим его сразу
  // при открытии сайта: пока человек выбирает файл, сервер успевает проснуться.
  // Ответ не нужен, ошибка не важна - это только «будильник»
  api.get(API_ENDPOINTS.health).catch(() => undefined);
});
