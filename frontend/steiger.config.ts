// Линтер Feature-Sliced Design: проверяет правила слоёв и публичные index.ts слайсов
import fsd from '@feature-sliced/steiger-plugin';
import { defineConfig } from 'steiger';

export default defineConfig([
  ...fsd.configs.recommended,
  {
    // Слои FSD лежат в app/ рядом с файлами Nuxt (layouts, assets, app.vue) - их не проверяем
    ignores: ['./app/layouts/**', './app/assets/**', './app/plugins/**', './app/app.vue', './app/**/README.md'],
  },
  {
    // В Nuxt pages/index.vue - это главная страница сайта, а не «публичный вход» слоя
    files: ['./app/pages/**'],
    rules: { 'fsd/no-layer-public-api': 'off' },
  },
]);
