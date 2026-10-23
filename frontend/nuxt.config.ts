// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/eslint'],

  // SPA: страница работает после загрузки файла, поисковикам она не нужна -
  // собираем статику (nuxt generate) и раздаём с CDN, без серверного рендеринга
  ssr: false,

  // FSD: компоненты и наши composables/утилиты импортируются явно,
  // через публичный index.ts слайса. Встроенные ref, computed, useRoute остаются автоматическими
  components: { dirs: [] },
  imports: { scan: false },

  // Адрес API. Локально - сервер FastAPI на 8000 порту, при сборке для сервера
  // задаётся переменной окружения NUXT_PUBLIC_API_URL
  runtimeConfig: {
    public: {
      apiUrl: 'http://localhost:8000',
    },
  },

  // Глобальные стили: дизайн-токены (_variables) и сброс браузерных стилей (_reset)
  css: ['~/assets/styles/main.scss'],

  // Миксины (respond-to, text, ellipsis...) доступны в каждом <style lang="scss" module> без импорта
  vite: {
    css: {
      preprocessorOptions: {
        scss: { additionalData: '@use "~/assets/styles/mixins" as *;\n' },
      },
    },
  },

  app: {
    head: {
      title: 'AI-аналитик для малого бизнеса',
      htmlAttrs: { lang: 'ru' },
      meta: [
        { name: 'description', content: 'Аналитика и прогноз продаж по выгрузке из Excel или CSV' },
      ],
    },
  },
})
