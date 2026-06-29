import { expect, test } from '@playwright/test';

test.describe('Dashboard', () => {
  test('unauthenticated users are redirected from dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('health endpoint returns ok', async ({ request }) => {
    const response = await request.get('/api/health');
    expect(response.ok()).toBeTruthy();
    const body = (await response.json()) as { status: string };
    expect(body.status).toBe('ok');
  });
});
