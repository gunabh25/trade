import { FlatCompat } from '@eslint/eslintrc';
import base from '@tradeflow/config/eslint/base';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const compat = new FlatCompat({
  baseDirectory: dirname(fileURLToPath(import.meta.url)),
});

/** @type {import('eslint').Linter.Config[]} */
export default [
  {
    ignores: [
      '.next/**',
      'next-env.d.ts',
      'eslint.config.mjs',
      'postcss.config.mjs',
      '**/playwright.config.ts',
      '**/vitest.config.ts',
      '**/vitest.setup.ts',
      'e2e/**',
      '**/*.test.ts',
      '**/*.test.tsx',
    ],
  },
  {
    settings: {
      next: {
        rootDir: 'apps/web',
      },
    },
  },
  ...base,
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: dirname(fileURLToPath(import.meta.url)),
      },
    },
  },
];
