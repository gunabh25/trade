import { defineConfig, devices } from '@playwright/test';

const PORT = Number(process.env.PORT) || 3000;
const baseURL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  ...(process.env.CI ? { workers: 1 } : {}),
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: process.env.CI
      ? [
          'pnpm exec next build',
          'cp -r .next/static .next/standalone/apps/web/.next/static',
          'cp -r public .next/standalone/apps/web/public',
          `PORT=${PORT} HOSTNAME=127.0.0.1 node .next/standalone/apps/web/server.js`,
        ].join(' && ')
      : 'pnpm dev',
    url: `${baseURL}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
