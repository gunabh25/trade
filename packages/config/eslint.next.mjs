import base from './eslint.base.mjs';
import nextPlugin from 'eslint-config-next/core-web-vitals.js';

/** @type {import('eslint').Linter.Config[]} */
export default [...base, ...nextPlugin];
