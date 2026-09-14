import { test, expect } from '@playwright/test';
test('scanner validates without opening a URL', async ({ page }) => { await page.goto('/'); await page.getByRole('button', { name: /check link/i }).click(); await expect(page.getByRole('alert')).toContainText('complete HTTP'); });
