import { test, expect } from '@playwright/test';
const settled = async (page) => {
  await expect(page.locator('#view')).toHaveAttribute('aria-busy', 'false');
};
test('all seven real-data views render without overflow or runtime errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await settled(page);
  for (const hash of ['overview', 'demand', 'zones', 'weather', 'quality', 'runs', 'methodology']) {
    await page.goto('/#' + hash);
    await settled(page);
    await expect(page.locator('main h1')).toBeVisible();
    await expect(page.locator('#view .error')).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  }
  expect(errors).toEqual([]);
});
test('zone and date filters change real API results and reset', async ({ page }) => {
  await page.goto('/');
  await settled(page);
  const original = await page.locator('.kpi-value').first().textContent();
  await page.getByLabel('Pickup zone', { exact: true }).selectOption('161');
  await page.getByRole('button', { name: 'Apply view' }).click();
  await settled(page);
  await expect(page.locator('.kpi-value').first()).not.toHaveText(original);
  await page.getByRole('button', { name: 'Reset', exact: true }).click();
  await settled(page);
  await expect(page.locator('.kpi-value').first()).toHaveText(original);
  await page.getByLabel('From', { exact: true }).fill('2026-01-01');
  await page.getByLabel('Through', { exact: true }).fill('2026-01-02');
  await page.getByRole('button', { name: 'Apply view' }).click();
  await settled(page);
  await expect(page.locator('.kpi-value').first()).toHaveText('0');
  await expect(page.locator('.empty').first()).toBeVisible();
});
test('zone comparison and historical method are usable', async ({ page }) => {
  await page.goto('/#zones');
  await settled(page);
  await expect(page.locator('#comparison table')).toBeVisible();
  const before = await page.locator('#comparison').textContent();
  await page.locator('#compare-b').selectOption({ index: 2 });
  await page.getByRole('button', { name: 'Compare zones' }).click();
  await expect(page.locator('#comparison')).not.toHaveText(before);
  await page
    .getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: /Methodology/ })
    .click();
  await settled(page);
  await expect(page.getByRole('heading', { name: 'Weather is association' })).toBeVisible();
});
test('API interruption surfaces an error and retry recovers', async ({ page }) => {
  await page.goto('/');
  await settled(page);
  await page.route('**/api/summary?**', (route) =>
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Injected warehouse outage' }),
    }),
  );
  await page.getByRole('button', { name: 'Apply view' }).click();
  await settled(page);
  await expect(page.locator('.error')).toContainText('Injected warehouse outage');
  await page.unroute('**/api/summary?**');
  await page.getByRole('button', { name: 'Try again' }).click();
  await settled(page);
  await expect(page.locator('.kpi-value').first()).toBeVisible();
});
