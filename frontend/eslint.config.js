import pluginVue from 'eslint-plugin-vue';
import vueParser from 'vue-eslint-parser';
import tsParser from '@typescript-eslint/parser';

export default [
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        sourceType: 'module',
      },
    },
  },
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsParser,
      sourceType: 'module',
    },
  },
  {
    ignores: ['dist/**', 'node_modules/**', 'src/types/generated/**', 'vite.config.ts.timestamp*'],
  },
  {
    rules: {
      'vue/multi-word-component-names': 'off',
    },
  },
];
