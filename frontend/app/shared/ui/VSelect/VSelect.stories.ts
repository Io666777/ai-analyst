import type { Meta, StoryObj } from '@storybook/vue3-vite';
import { ref } from 'vue';
import type { SelectOption } from './types';
import VSelect from './VSelect.vue';

// Роли колонок - как их отдаёт API (/api/options)
const ROLES: SelectOption[] = [
  { value: 'date', label: 'дата' },
  { value: 'object', label: 'товар / услуга' },
  { value: 'category', label: 'категория' },
  { value: 'quantity', label: 'количество' },
  { value: 'amount', label: 'сумма, деньги' },
  { value: 'price', label: 'цена за единицу (если суммы нет - посчитается сама)' },
  { value: 'person', label: 'клиент (в анализ не попадёт)' },
  { value: 'ignore', label: 'не нужна' },
];

const meta = {
  title: 'shared/ui/VSelect',
  component: VSelect,
  args: {
    label: 'Колонка «Дата чека»',
    options: ROLES,
    modelValue: '',
    placeholder: 'Выберите роль',
    disabled: false,
    required: false,
  },
  // v-model внутри истории: значение меняется, когда выбираешь вариант
  render: args => ({
    components: { VSelect },
    setup: () => {
      const value = ref(args.modelValue);
      return { args, value };
    },
    template: '<VSelect v-bind="args" v-model="value" style="max-width: 20rem" />',
  }),
} satisfies Meta<typeof VSelect>;

export default meta;

type Story = StoryObj<typeof meta>;

/** Ничего не выбрано - серая подсказка. */
export const Empty: Story = {};

export const Selected: Story = {
  args: { modelValue: 'date', hint: 'Примеры: 01.10.24, 02.10.24, 03.10.24' },
};

/** Длинный вариант обрезается многоточием, а не распирает поле. */
export const LongOption: Story = {
  args: { label: 'Колонка «Цена»', modelValue: 'price' },
};

export const WithError: Story = {
  args: { required: true, error: 'Укажите, где дата - без неё события не привязать ко времени' },
};

/** Не ошибка, а просьба проверить: программа угадала роль неуверенно. */
export const WithWarning: Story = {
  args: {
    label: 'Колонка «Сумма2»',
    modelValue: 'amount',
    warning: 'Проверьте - угадано наугад. Примеры: 120, 85, 40',
  },
};

export const Disabled: Story = {
  args: { modelValue: 'amount', disabled: true },
};
