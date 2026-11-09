/* eslint-env node */
// 轻量 ESLint 配置：让 npm run lint 可用（此前仓库只有脚本没有配置，运行即报错）。
// 规则从宽：本项目 vue-tsc + vitest 已承担类型/行为校验，eslint 只做基础静态检查。
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 'latest',
    sourceType: 'module',
    extraFileExtensions: ['.vue'],
  },
  ignorePatterns: [
    'dist/**',
    'node_modules/**',
    'python311/**',
    'src/auto-imports.d.ts',
    'src/vite-env.d.ts',
  ],
  rules: {
    'vue/multi-word-component-names': 'off',
    'vue/require-default-prop': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
  },
}
