// Общее для всех историй: глобальные стили (токены и сброс) - как на сайте
import type { Preview } from '@storybook/vue3-vite';

import '../app/assets/styles/main.scss';

const preview: Preview = {
  parameters: {
    layout: 'padded',
    controls: { expanded: true },
    a11y: { test: 'error' }, // нарушение доступности - ошибка, а не тихое предупреждение
  },
  tags: ['autodocs'], // страница документации для каждого компонента
};

export default preview;
