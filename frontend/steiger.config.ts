// Линтер Feature-Sliced Design: проверяет правила слоёв и публичные index.ts слайсов
import fsd from '@feature-sliced/steiger-plugin';
import { defineConfig } from 'steiger';

export default defineConfig([
  ...fsd.configs.recommended,
  {
    // Слои FSD лежат в app/ рядом с файлами Nuxt (layouts, middleware, assets, app.vue) -
    // их не проверяем
    ignores: [
      './app/layouts/**',
      './app/middleware/**',
      './app/assets/**',
      './app/plugins/**',
      './app/app.vue',
      './app/**/README.md',
    ],
  },
  {
    // В Nuxt pages - это адреса сайта: pages/index.vue - главная, а не «публичный вход» слоя,
    // pages/analysis/ - часть адреса /analysis/..., а не слайс с сегментами
    files: ['./app/pages/**'],
    rules: { 'fsd/no-layer-public-api': 'off', 'fsd/no-segmentless-slices': 'off' },
  },
  {
    // «Слайс используется в одном месте или нигде» - предупреждение, а не ошибка:
    // ссылки из app/plugins Steiger не видит (папка вне проверки), а на старте проекта
    // у многих слайсов пока одна ссылка. Предупреждения всё равно видны в npm run lint:fsd
    rules: { 'fsd/insignificant-slice': 'warn' },
  },
]);
