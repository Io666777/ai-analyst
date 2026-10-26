// Правила кода - по CLAUDE_Front.md (раздел Javascript/Typescript и Vue)
import withNuxt from './.nuxt/eslint.config.mjs';

export default withNuxt({
  rules: {
    // Только строгое сравнение ===
    'eqeqeq': ['error', 'always'],
    // Никаких забытых console.log и debugger
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'error',
    // async/await вместо цепочек then
    'prefer-promise-reject-errors': 'error',
    // Имена компонентов в шаблоне - PascalCase
    'vue/component-name-in-template-casing': ['error', 'PascalCase'],
    // v-html - только когда без него никак
    'vue/no-v-html': 'warn',
  },
});
