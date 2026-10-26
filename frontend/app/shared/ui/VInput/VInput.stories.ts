import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { ref } from 'vue';
import { INPUT_TYPES } from './constants';
import VInput from './VInput.vue';

const meta = {
  title: 'shared/ui/VInput',
  component: VInput,
  args: {
    label: 'Товар',
    modelValue: '',
    type: INPUT_TYPES.text,
    placeholder: 'Например, пиво',
    disabled: false,
    required: false,
  },
  argTypes: {
    type: { control: 'inline-radio', options: Object.values(INPUT_TYPES) },
  },
  // v-model внутри истории: значение меняется, когда печатаешь в поле
  render: args => ({
    components: { VInput },
    setup: () => {
      const value = ref(args.modelValue);
      return { args, value };
    },
    template: '<VInput v-bind="args" v-model="value" style="max-width: 20rem" />',
  }),
} satisfies Meta<typeof VInput>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithHint: Story = {
  args: { hint: 'Название, его часть или артикул' },
};

/** Ошибка вместо подсказки: красная рамка, текст читает экранный диктор. */
export const WithError: Story = {
  args: { label: 'Валюта', placeholder: undefined, error: 'Укажите валюту: р., $, £...' },
};

export const Required: Story = {
  args: { label: 'Валюта', placeholder: 'р.', required: true },
};

export const Disabled: Story = {
  args: { label: 'Файл', modelValue: 'shop.xlsx', disabled: true },
};

export const Date: Story = {
  args: { label: 'Период с', type: INPUT_TYPES.date, modelValue: '2026-09-01', placeholder: undefined },
};

export const Search: Story = {
  args: { type: INPUT_TYPES.search, hint: 'Название, его часть или артикул' },
};
