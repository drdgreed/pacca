/**
 * PACCA frontend smoke test.
 *
 * Verifies the Editorial-Clinical aesthetic loads everywhere (per
 * PR-UI-1 onward — the theme is global, not scoped). Checks SME-author
 * routes resolve, the editorial nav renders, and skip-link a11y works.
 *
 * Uses route mocking for the backend — no FastAPI server needed.
 *
 * To run:
 *   cd frontend
 *   npx playwright install --with-deps chromium    # one-time
 *   npx playwright test
 */

import { expect, test } from '@playwright/test';

// Synthetic JWT (no signature — just a shape the frontend accepts in
// localStorage. The mocked backend doesn't verify it).
const SYNTHETIC_TOKEN = 'eyJ.smoke-test.token';

test.beforeEach(async ({ page }) => {
  // Seed localStorage before any navigation so <RequireAuth> passes
  await page.addInitScript((token) => {
    window.localStorage.setItem('token', token);
  }, SYNTHETIC_TOKEN);

  // Mock the SME-authoring endpoints that the dashboard calls on load
  await page.route('**/api/v1/sme-authoring/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        kind: 'status',
        total_cases: 100,
        per_list_counts: [
          {
            list_name: 'oncology_cases',
            file: 'tests/clinical/oncology_cases.py',
            count: 28,
            id_range: 'GC-001 – GC-028',
          },
        ],
        milestone_gaps: [],
        coverage_parsed_ok: true,
        coverage_parse_error: '',
      }),
    });
  });

  await page.route('**/api/v1/sme-authoring/sessions', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ kind: 'session_list', sessions: [], total: 0 }),
    });
  });

  await page.route('**/api/v1/sme-authoring/gaps', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ kind: 'gap_list', gaps: [], total: 0 }),
    });
  });
});

test.describe('PACCA frontend smoke', () => {
  test('SME dashboard renders with editorial aesthetic', async ({ page }) => {
    await page.goto('/sme-author');

    await expect(
      page.getByRole('heading', { name: 'SME Case Authoring' }),
    ).toBeVisible();

    // Total-case count should render the mocked 100.
    await expect(page.getByText('100', { exact: true })).toBeVisible();

    // Editorial-Clinical aesthetic spot-check: body should use Source Serif 4.
    const bodyFont = await page.evaluate(() =>
      getComputedStyle(document.body).fontFamily,
    );
    expect(bodyFont).toContain('Source Serif');

    // No console errors during render
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.waitForLoadState('networkidle');
    expect(errors).toEqual([]);
  });

  test('primary nav links surface all four PACCA tabs', async ({ page }) => {
    await page.goto('/sme-author');

    // The new AppLayout's EditorialNav surfaces all four surfaces.
    await expect(page.getByRole('link', { name: 'Submit case' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Director queue' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Admin' })).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'SME authoring' }).first(),
    ).toBeVisible();
  });

  test('SME secondary nav links resolve to their routes', async ({ page }) => {
    await page.goto('/sme-author');

    await page.getByRole('link', { name: 'New case' }).first().click();
    await expect(page).toHaveURL(/\/sme-author\/new$/);

    await page.getByRole('link', { name: 'Dashboard' }).first().click();
    await expect(page).toHaveURL(/\/sme-author$/);

    await page.getByRole('link', { name: 'Sessions' }).first().click();
    await expect(page).toHaveURL(/\/sme-author\/sessions$/);
  });

  test('skip-to-content link is keyboard-accessible', async ({ page }) => {
    await page.goto('/sme-author');

    // Tab from the top — the first focusable element should be the skip link
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => {
      const el = document.activeElement;
      return el ? { tag: el.tagName, text: el.textContent } : null;
    });
    expect(focused?.text).toContain('Skip to main content');
  });

  test('editorial theme applies everywhere: provider route also uses Source Serif', async ({
    page,
  }) => {
    // Pre-PR-UI-1: this test asserted .sme-authoring class was ABSENT on
    // /provider (aesthetic isolation). After PR-UI-1 the theme is global,
    // so the inverse assertion now holds — every authenticated route
    // shares the same body font + editorial nav.
    await page.route('**/api/v1/authorizations*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10 }),
      });
    });

    await page.goto('/provider');

    const bodyFont = await page.evaluate(() =>
      getComputedStyle(document.body).fontFamily,
    );
    expect(bodyFont).toContain('Source Serif');

    // The primary EditorialNav should be present on /provider too.
    await expect(
      page.getByRole('navigation', { name: 'Primary navigation' }),
    ).toBeVisible();
  });

  test('login screen renders in editorial aesthetic', async ({ page }) => {
    // Clear the seeded token so we land on /login
    await page.addInitScript(() => window.localStorage.removeItem('token'));
    await page.goto('/login');

    await expect(page.getByRole('heading', { name: 'PACCA' })).toBeVisible();
    await expect(page.getByLabel('Username')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });
});
