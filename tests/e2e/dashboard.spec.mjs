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

test('date shortcuts, chart inspection and CSV export preserve the selected data', async ({
  page,
}) => {
  await page.goto('/');
  await settled(page);
  const meta = await (await page.request.get('/api/meta')).json();
  const end = meta.coverage.end;
  const week = new Date(end + 'T12:00:00Z');
  week.setUTCDate(week.getUTCDate() - 6);
  const start = [meta.coverage.start, week.toISOString().slice(0, 10)].sort().at(-1);
  await page.getByRole('button', { name: 'Last 7 days', exact: true }).click();
  await settled(page);
  await expect(page.getByLabel('From', { exact: true })).toHaveValue(start);
  await expect(page.getByLabel('Through', { exact: true })).toHaveValue(end);
  await expect(page.getByRole('button', { name: 'Last 7 days', exact: true })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
  await page.getByLabel('Pickup zone', { exact: true }).selectOption('161');
  await page.getByRole('button', { name: 'Apply view' }).click();
  await settled(page);
  const response = await page.request.get(`/api/summary?start=${start}&end=${end}&zone=161`);
  const summary = await response.json();
  await page.getByRole('button', { name: 'Cumulative', exact: true }).click();
  await expect(page.locator('.chart-readout')).toContainText(
    summary.observed_trips.toLocaleString('en-US'),
  );
  await expect(page.getByRole('button', { name: 'Cumulative', exact: true })).toBeFocused();
  await page.locator('[data-chart-date]').first().focus();
  await expect(page.locator('.chart-readout')).toContainText(
    new Date(start + 'T12:00:00Z').toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      timeZone: 'UTC',
    }),
  );
  const downloaded = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export daily data' }).click();
  const file = await downloaded;
  expect(file.suggestedFilename()).toBe(`atlasiq-daily-${start}-${end}-zone-161.csv`);
  const { readFile } = await import('node:fs/promises');
  const csv = await readFile(await file.path(), 'utf8');
  const rows = csv.trim().split(/\r?\n/);
  expect(rows[0]).toBe('nyc_pickup_date,observed_sample_trips,average_base_fare_usd');
  expect(rows).toHaveLength(8);
  expect(rows.slice(1).reduce((sum, row) => sum + Number(row.split(',')[1]), 0)).toBe(
    summary.observed_trips,
  );
  await page.getByRole('button', { name: 'Full coverage', exact: true }).click();
  await settled(page);
  await expect(page.getByLabel('From', { exact: true })).toHaveValue(meta.coverage.start);
});

test('a cross-month view reconciles daily results with the displayed total', async ({ page }) => {
  await page.goto('/');
  await settled(page);
  const meta = await (await page.request.get('/api/meta')).json();
  const partitions = [...meta.partitions].sort((a, b) => a.month.localeCompare(b.month));
  test.skip(partitions.length < 2, 'Requires the documented multi-month backfill.');
  const boundary = new Date(partitions[1].month.slice(0, 10) + 'T12:00:00Z');
  const end = boundary.toISOString().slice(0, 10);
  boundary.setUTCDate(boundary.getUTCDate() - 1);
  const start = boundary.toISOString().slice(0, 10);
  await page.getByLabel('From', { exact: true }).fill(start);
  await page.getByLabel('Through', { exact: true }).fill(end);
  await page.getByRole('button', { name: 'Apply view' }).click();
  await settled(page);
  const trends = await (await page.request.get(`/api/trends?start=${start}&end=${end}`)).json();
  expect(trends.map((r) => r.date)).toEqual([start, end]);
  const count = trends.reduce((sum, r) => sum + r.observed_trips, 0);
  expect(count).toBeGreaterThan(0);
  await expect(page.locator('.kpi-value').first()).toHaveText(count.toLocaleString('en-US'));
  await expect(page.locator('[data-chart-date]')).toHaveCount(2);
  await page.getByRole('button', { name: 'Reset', exact: true }).click();
  await settled(page);
  await expect(page.getByLabel('From', { exact: true })).toHaveValue(meta.coverage.start);
  await expect(page.getByLabel('Through', { exact: true })).toHaveValue(meta.coverage.end);
});
