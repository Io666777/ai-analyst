import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { METRIC_FORMATS } from './constants';
import VMetric from './VMetric.vue';

const meta = {
  title: 'shared/ui/VMetric',
  component: VMetric,
  args: {
    label: 'Выручка: сентябрь 2026',
    value: 18739.8,
    format: METRIC_FORMATS.money,
    currency: 'р.',
    change: -7.6,
    changeLabel: 'к прошлому месяцу',
  },
  argTypes: {
    format: { control: 'inline-radio', options: Object.values(METRIC_FORMATS) },
  },
} satisfies Meta<typeof VMetric>;

export default meta;

type Story = StoryObj<typeof meta>;

/** Падение - красным со стрелкой вниз. */
export const Decline: Story = {};

/** Рост - зелёным со стрелкой вверх. */
export const Growth: Story = {
  args: { label: 'В среднем в день', value: 821.57, change: 7.2, changeLabel: 'к январю' },
};

/** Ноль - серым: без изменений. */
export const NoChange: Story = {
  args: { change: 0 },
};

/** null с сервера: в прошлом периоде было 0 - процент не посчитать (это не «без изменений»). */
export const Unknown: Story = {
  args: { change: null },
};

/** Без изменения - только цифра. */
export const ValueOnly: Story = {
  args: { label: 'Итог прогноза на 90 дн.', value: 63123.5, change: undefined, hint: 'Коридор: 54 352 р. - 71 889 р.' },
};

export const NumberFormat: Story = {
  args: { label: 'Продано штук', value: 39716, format: METRIC_FORMATS.number, change: undefined },
};

export const PercentFormat: Story = {
  args: { label: 'Доля выручки', value: 27.5, format: METRIC_FORMATS.percent, change: undefined },
};

/** Три цифры в ряд - как на экране обзора (данные из /api/analysis/overview). */
export const OverviewRow: Story = {
  render: () => ({
    components: { VMetric },
    template: `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); gap: 1.5rem">
        <VMetric label="Выручка: сентябрь 2026" :value="18739.8" :change="-7.6" change-label="к прошлому месяцу" />
        <VMetric label="В среднем в день" :value="624.66" :change="-4.5" />
        <VMetric label="Выручка: август 2026" :value="20274.8" />
      </div>
    `,
  }),
};
