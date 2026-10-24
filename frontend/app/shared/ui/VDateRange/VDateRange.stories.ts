import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { ref } from 'vue';
import VDateRange from './VDateRange.vue';

const meta = {
  title: 'shared/ui/VDateRange',
  component: VDateRange,
  args: {
    modelValue: { from: '2026-09-01', to: '2026-09-30' },
    label: 'Стало',
    min: '2024-10-01',
    max: '2026-09-30',
  },
} satisfies Meta<typeof VDateRange>;

export default meta;

type Story = StoryObj<typeof meta>;

/** Протяните мышью по дням - или нажмите первый и последний день. */
export const Default: Story = {
  render: args => ({
    components: { VDateRange },
    setup() {
      const period = ref(args.modelValue);
      return { args, period };
    },
    template: `
      <div style="max-width: 20rem; min-height: 26rem">
        <VDateRange v-bind="args" v-model="period" />
        <p style="margin-top: 1rem">Выбрано: {{ period.from || '-' }} … {{ period.to || '-' }}</p>
      </div>
    `,
  }),
};

/** Период можно сбросить: в топе это «за всё время». */
export const Clearable: Story = {
  ...Default,
  args: {
    modelValue: { from: '', to: '' },
    label: 'Период',
    placeholder: 'За всё время',
    clearable: true,
    clearLabel: 'За всё время',
    max: '2026-09-30',
  },
};

export const WithError: Story = {
  ...Default,
  args: { error: 'Выберите период' , modelValue: { from: '', to: '' } },
};
