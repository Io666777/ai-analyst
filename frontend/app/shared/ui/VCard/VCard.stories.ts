import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { BUTTON_SIZES, BUTTON_VARIANTS, VButton } from '../VButton';
import VCard from './VCard.vue';

const meta = {
  title: 'shared/ui/VCard',
  component: VCard,
  args: { title: 'Выручка по месяцам', titleLevel: 2 },
  argTypes: { titleLevel: { control: 'inline-radio', options: [2, 3] } },
  render: args => ({
    components: { VCard, VButton },
    setup: () => ({ args, BUTTON_SIZES, BUTTON_VARIANTS }),
    template: `
      <VCard v-bind="args" style="max-width: 32rem">
        <template #actions>
          <VButton :variant="BUTTON_VARIANTS.ghost" :size="BUTTON_SIZES.small">Скачать PNG</VButton>
        </template>
        <p>Здесь будет график. Неполные месяцы на него не попадают - иначе месяц из 9 дней выглядел бы как обвал продаж.</p>
      </VCard>
    `,
  }),
} satisfies Meta<typeof VCard>;

export default meta;

type Story = StoryObj<typeof meta>;

export const WithTitleAndActions: Story = {};

/** Без заголовка - просто белая подложка. */
export const Plain: Story = {
  args: { title: undefined },
  render: args => ({
    components: { VCard },
    setup: () => ({ args }),
    template: '<VCard v-bind="args" style="max-width: 32rem"><p>Содержимое карточки</p></VCard>',
  }),
};
