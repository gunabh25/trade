const eslintFor = (configPath) => [
  `eslint --fix --max-warnings 0 --no-warn-ignored --config ${configPath}`,
  'prettier --write',
];

/** @type {import('lint-staged').Configuration} */
export default {
  'apps/web/**/*.{ts,tsx}': eslintFor('apps/web/eslint.config.mjs'),
  'packages/types/**/*.{ts,tsx}': eslintFor('packages/types/eslint.config.mjs'),
  'packages/ui/**/*.{ts,tsx}': eslintFor('packages/ui/eslint.config.mjs'),
  '*.{js,jsx,mjs,cjs}': ['prettier --write'],
  '*.{json,md,css,yml,yaml}': ['prettier --write'],
  'apps/api/**/*.py': ['ruff check --fix', 'ruff format'],
};
