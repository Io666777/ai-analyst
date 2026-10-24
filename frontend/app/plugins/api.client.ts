// Слой app: при запуске настраиваем клиент API - откуда брать адрес сервера и номер сессии,
// и что делать, когда сервер сообщил «сессия устарела»: забыть сессию и вернуть на главную,
// где пользователь увидит «загрузите файл заново"
import { defineNuxtPlugin, navigateTo, useRuntimeConfig } from '#imports';
import { useSession } from '~/entities/session';
import { configureApiClient } from '~/shared/api';
import { ROUTES } from '~/shared/config';

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
});
