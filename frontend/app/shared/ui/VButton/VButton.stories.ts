import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { fn } from 'storybook/test';
import { BUTTON_SIZES, BUTTON_VARIANTS } from './constants';
import VButton from './VButton.vue';

const meta = {
  title: 'shared/ui/VButton',
  component: VButton,
  args: {
    variant: BUTTON_VARIANTS.primary,
    size: BUTTON_SIZES.medium,
    type: 'button',
    disabled: false,
    loading: false,
    onClick: fn(), // нажатия видны во вкладке Actions
  },
  argTypes: {
    variant: { control: 'inline-radio', options: Object.values(BUTTON_VARIANTS) },
    size: { control: 'inline-radio', options: Object.values(BUTTON_SIZES) },
    type: { control: 'inline-radio', options: ['button', 'submit'] },
  },
  render: args => ({
    components: { VButton },
    setup: () => ({ args }),
    template: '<VButton v-bind="args">Посчитать прогноз</VButton>',
  }),
} satisfies Meta<typeof VButton>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Primary: Story = {};

export const Secondary: Story = {
  args: { variant: BUTTON_VARIANTS.secondary },
};

export const Ghost: Story = {
  args: { variant: BUTTON_VARIANTS.ghost },
};

export const Small: Story = {
  args: { size: BUTTON_SIZES.small },
};

export const Disabled: Story = {
  args: { disabled: true },
};

/** Идёт загрузка: спиннер, кнопка не нажимается - двойной клик не отправит запрос дважды. */
export const Loading: Story = {
  args: { loading: true },
};

/** Все виды и состояния рядом - для сравнения. */
export const AllVariants: Story = {
  render: () => ({
    components: { VButton },
    setup: () => ({ BUTTON_VARIANTS, BUTTON_SIZES }),
    template: `
      <div style="display: grid; gap: 0.75rem">
        <div v-for="variant in BUTTON_VARIANTS" :key="variant" style="display: flex; gap: 0.75rem">
          <VButton :variant="variant">{{ variant }}</VButton>
          <VButton :variant="variant" :size="BUTTON_SIZES.small">small</VButton>
          <VButton :variant="variant" disabled>disabled</VButton>
          <VButton :variant="variant" loading>loading</VButton>
        </div>
      </div>
    `,
  }),
};
