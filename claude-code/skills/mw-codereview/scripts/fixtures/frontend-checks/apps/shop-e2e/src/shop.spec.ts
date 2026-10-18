import { expect, test } from '@playwright/test';

test('lists the orders', async ({ page }) => {
  await page.goto('/orders');
  await expect(page.getByRole('heading')).toBeVisible();
});
