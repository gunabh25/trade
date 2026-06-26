/** @type {import('lint-staged').Configuration} */
export default {
  '*.{ts,tsx}': ['eslint --fix --max-warnings 0', 'prettier --write'],
  '*.{js,jsx,mjs,cjs}': ['prettier --write'],
  '*.{json,md,css,yml,yaml}': ['prettier --write'],
  'apps/api/**/*.py': ['ruff check --fix', 'ruff format'],
};
