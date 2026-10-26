import type { Meta, StoryObj } from '@storybook/vue3-vite';
import VFormField from './VFormField.vue';

const meta = {
  title: 'shared/ui/VFormField',
  component: VFormField,
  args: {
    label: 'Комментарий',
    hint: 'Обвязка для любого поля: подпись, подсказка или ошибка',
    required: false,
  },
  // В слот вставляется любое поле - здесь обычная textarea
  render: args => ({
    components: { VFormField },
    setup: () => ({ args }),
    template: `
      <VFormField v-bind="args" v-slot="{ id, describedBy, invalid }" style="max-width: 20rem">
        <textarea
          :id="id"
          :aria-describedby="describedBy"
          :aria-invalid="invalid"
          rows="3"
          style="width: 100%"
        />
      </VFormField>
    `,
  }),
} satisfies Meta<typeof VFormField>;

export default meta;

type Story = StoryObj<typeof meta>;

export const WithHint: Story = {};

export const WithError: Story = {
  args: { hint: undefined, error: 'Слишком длинный комментарий', required: true },
};
