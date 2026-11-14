import { test, expect } from '@playwright/test';

test('basic page load test', async ({ page }) => {
  await page.goto('https://example.com');
  await expect(page).toHaveTitle(/Example Domain/);
});

test('search functionality test', async ({ page }) => {
  await page.goto('https://www.google.com');
  // Note: Google's selector might change, but this is a basic connectivity check
  const searchBox = page.locator('textarea[name="q"]');
  await expect(searchBox).toBeVisible();
});
