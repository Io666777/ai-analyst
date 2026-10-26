// Storybook - витрина базовых компонентов shared/ui: все состояния, документация, проверка доступности.
// Запуск: npm run storybook -> http://localhost:6006
import { fileURLToPath } from 'node:url';
import type { StorybookConfig } from '@storybook/vue3-vite';
import vue from '@vitejs/plugin-vue';
import { mergeConfig } from 'vite';

const APP_DIR = fileURLToPath(new URL('../app', import.meta.url));

const config: StorybookConfig = {
  stories: ['../app/**/*.stories.ts'],
  addons: ['@storybook/addon-docs', '@storybook/addon-a11y'],
  // vue-component-meta читает пропсы и JSDoc для страницы Docs (старый vue-docgen-api устарел)
  framework: { name: '@storybook/vue3-vite', options: { docgen: 'vue-component-meta' } },

  // Storybook собирает компоненты без Nuxt - повторяем то, что Nuxt даёт сам:
  // поддержку .vue-файлов, путь ~ к папке app и миксины в каждом <style lang="scss">
  viteFinal: config =>
    mergeConfig(config, {
      plugins: [vue()],
      resolve: { alias: { '~': APP_DIR } },
      css: {
        preprocessorOptions: {
          scss: { additionalData: '@use "~/assets/styles/mixins" as *;\n' },
        },
      },
    }),
};

export default config;
