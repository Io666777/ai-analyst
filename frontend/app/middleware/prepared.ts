// Защита разделов анализа: без размеченных данных считать нечего - на главную.
// Подключается на странице: definePageMeta({ middleware: 'prepared' })
import { defineNuxtRouteMiddleware, navigateTo } from '#imports';
import { useSession } from '~/entities/session';
import { ROUTES } from '~/shared/config';

export default defineNuxtRouteMiddleware(() => {
  const session = useSession();
  if (!session.isPrepared.value) return navigateTo(ROUTES.home, { replace: true });
});
