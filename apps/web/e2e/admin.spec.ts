import { expect, test } from '@playwright/test';

test.describe('Admin panel', () => {
  test('admin routes require authentication', async ({ page }) => {
    await page.goto('/admin');
    await expect(page).toHaveURL(/\/login/);
  });

  test('admin users page redirects unauthenticated visitors', async ({ page }) => {
    await page.goto('/admin/users');
    await expect(page).toHaveURL(/\/login/);
  });
});
