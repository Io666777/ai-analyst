import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { fn } from 'storybook/test';
import VFileDrop from './VFileDrop.vue';

const meta = {
  title: 'shared/ui/VFileDrop',
  component: VFileDrop,
  args: {
    accept: '.csv,.xlsx,.xls',
    label: 'Перетащите файл сюда или нажмите, чтобы выбрать',
    hint: 'Excel (.xlsx, .xls) или CSV, до 20 МБ',
    disabled: false,
    loading: false,
    onSelect: fn(), // выбранный файл виден во вкладке Actions
  },
  render: args => ({
    components: { VFileDrop },
    setup: () => ({ args }),
    template: '<VFileDrop v-bind="args" style="max-width: 32rem" />',
  }),
} satisfies Meta<typeof VFileDrop>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};

/** Файл отправляется - спиннер вместо надписи, поле не нажимается. */
export const Loading: Story = {
  args: { loading: true },
};

export const Disabled: Story = {
  args: { disabled: true },
};
