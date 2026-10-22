// Правила стилей - по CLAUDE_Front.md (раздел CSS и Code Style)
export default {
  extends: ['stylelint-config-standard-scss', 'stylelint-config-recommended-vue/scss'],
  rules: {
    // Классы CSS-модулей: корневой - PascalCase (= имя компонента), остальные - camelCase,
    // модификаторы - через подчёркивание: _active, _disabled
    'selector-class-pattern': [
      '^(_?[a-z][a-zA-Z0-9]*|[A-Z][a-zA-Z0-9]*)$',
      { message: 'Класс: PascalCase для корня, camelCase для элементов, _camelCase для модификаторов' },
    ],
    // Цвета - только через переменные: var(--primary-500)
    'color-named': 'never',
    'color-no-hex': [true, { message: 'Цвет - только через переменную из main.scss' }],
    // !important - только для вендорных стилей
    'declaration-no-important': true,
    // Переменные группируются пустыми строками с комментарием: основной цвет, акцент, нейтральные...
    'custom-property-empty-line-before': null,
    // :global и :export из CSS-модулей
    'selector-pseudo-class-no-unknown': [true, { ignorePseudoClasses: ['global', 'export'] }],
  },
  overrides: [
    {
      // Переменные цветов объявляются только здесь
      files: ['app/assets/styles/main.scss'],
      rules: { 'color-no-hex': null },
    },
  ],
};
