import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { VButton } from '../VButton';
import { ALERT_VARIANTS } from './constants';
import VAlert from './VAlert.vue';

const meta = {
  title: 'shared/ui/VAlert',
  component: VAlert,
  args: { variant: ALERT_VARIANTS.info, title: undefined },
  argTypes: {
    variant: { control: 'inline-radio', options: Object.values(ALERT_VARIANTS) },
  },
  render: args => ({
    components: { VAlert },
    setup: () => ({ args }),
    template: `
      <VAlert v-bind="args" style="max-width: 32rem">
        Неполные месяцы не показаны: декабрь 2011 (данные по 09.12.2011)
      </VAlert>
    `,
  }),
} satisfies Meta<typeof VAlert>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Info: Story = {};

export const Success: Story = {
  args: { variant: ALERT_VARIANTS.success, title: 'Данные подготовлены' },
};

export const Warning: Story = {
  args: { variant: ALERT_VARIANTS.warning, title: 'Сравнение может быть неверным' },
};

/** Ошибка с действием: диктор читает её сразу. */
export const ErrorWithAction: Story = {
  args: { variant: ALERT_VARIANTS.error, title: 'Сессия устарела' },
  render: args => ({
    components: { VAlert, VButton },
    setup: () => ({ args }),
    template: `
      <VAlert v-bind="args" style="max-width: 32rem">
        Данные удалены с сервера через полчаса без работы - так они не хранятся дольше нужного.
        <template #actions><VButton>Загрузить файл заново</VButton></template>
      </VAlert>
    `,
  }),
};

/** Все виды рядом. */
export const AllVariants: Story = {
  render: () => ({
    components: { VAlert },
    setup: () => ({ ALERT_VARIANTS }),
    template: `
      <div style="display: grid; gap: 0.75rem; max-width: 32rem">
        <VAlert v-for="variant in ALERT_VARIANTS" :key="variant" :variant="variant" :title="variant">
          Текст сообщения
        </VAlert>
      </div>
    `,
  }),
};
