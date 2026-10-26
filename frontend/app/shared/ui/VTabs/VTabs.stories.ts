import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { ref } from 'vue';
import VTabs from './VTabs.vue';

const meta = {
  title: 'shared/ui/VTabs',
  component: VTabs,
  args: {
    modelValue: 'items',
    label: 'Подробности месяца',
    tabs: [
      { value: 'items', label: 'Товары' },
      { value: 'days', label: 'По дням' },
    ],
  },
} satisfies Meta<typeof VTabs>;

export default meta;

type Story = StoryObj<typeof meta>;

/** Клик или стрелки ← → переключают вкладку; содержимое - в слоте. */
export const Default: Story = {
  render: args => ({
    components: { VTabs },
    setup() {
      const view = ref(args.modelValue);
      return { args, view };
    },
    template: `
      <VTabs v-bind="args" v-model="view">
        <p v-if="view === 'items'">Пиво Лидское 0.5 - 5 271 р., Чипсы Lays - 2 890 р.</p>
        <p v-else>01.09 - 612 р., 02.09 - 640 р., 03.09 - 598 р.</p>
      </VTabs>
    `,
  }),
};
