import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { SPINNER_SIZES } from './constants';
import VSpinner from './VSpinner.vue';

const meta = {
  title: 'shared/ui/VSpinner',
  component: VSpinner,
  args: {
    size: SPINNER_SIZES.medium,
    label: 'Считаю прогноз: проверяю модели на прошлом...',
    showLabel: true,
    decorative: false,
  },
  argTypes: {
    size: { control: 'inline-radio', options: Object.values(SPINNER_SIZES) },
  },
  // Цвет спиннера - от текста вокруг: в блоке он синий
  render: args => ({
    components: { VSpinner },
    setup: () => ({ args }),
    template: '<div style="color: var(--primary-500)"><VSpinner v-bind="args" /></div>',
  }),
} satisfies Meta<typeof VSpinner>;

export default meta;

type Story = StoryObj<typeof meta>;

export const WithLabel: Story = {};

/** Подпись только для диктора. */
export const Silent: Story = {
  args: { showLabel: false },
};

export const Large: Story = {
  args: { size: SPINNER_SIZES.large, label: 'Читаю файл...' },
};
