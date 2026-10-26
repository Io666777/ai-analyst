import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { ref } from 'vue';
import VCheckbox from './VCheckbox.vue';

const meta = {
  title: 'shared/ui/VCheckbox',
  component: VCheckbox,
  args: {
    label: 'Худшие вместо лучших',
    modelValue: false,
    disabled: false,
  },
  // v-model внутри истории: флажок переключается по клику
  render: args => ({
    components: { VCheckbox },
    setup: () => {
      const checked = ref(args.modelValue);
      return { args, checked };
    },
    template: '<VCheckbox v-bind="args" v-model="checked" />',
  }),
} satisfies Meta<typeof VCheckbox>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Unchecked: Story = {};

export const Checked: Story = {
  args: { modelValue: true },
};

export const Disabled: Story = {
  args: { disabled: true, modelValue: true },
};

/** Длинная подпись переносится, квадратик остаётся у первой строки. */
export const LongLabel: Story = {
  args: {
    label: 'DOTCOM POSTAGE - похоже на плату за доставку, а не на товар. Не учитывать в анализе',
  },
  render: args => ({
    components: { VCheckbox },
    setup: () => ({ args, checked: ref(false) }),
    template: '<div style="max-width: 20rem"><VCheckbox v-bind="args" v-model="checked" /></div>',
  }),
};

/** Список флажков - так будет выглядеть выбор служебных строк. */
export const List: Story = {
  render: () => ({
    components: { VCheckbox },
    setup: () => ({
      names: ['DOTCOM POSTAGE', 'AMAZON FEE', 'Manual', 'CARRIAGE CLOCK'],
      excluded: ref<string[]>(['DOTCOM POSTAGE', 'AMAZON FEE']),
    }),
    template: `
      <div style="display: grid; gap: 0.25rem">
        <VCheckbox
          v-for="name in names"
          :key="name"
          :label="name"
          :model-value="excluded.includes(name)"
          @update:model-value="checked => (excluded = checked
            ? [...excluded, name]
            : excluded.filter(item => item !== name))"
        />
      </div>
    `,
  }),
};
