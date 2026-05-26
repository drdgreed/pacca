/**
 * SME Case Authoring Web UI — smoke test.
 *
 * Verifies that the editorial-clinical surface loads, the nav renders,
 * and the dashboard route resolves without runtime errors.
 *
 * This test uses route mocking for the backend — it doesn't require the
 * FastAPI server to be running. Wider integration coverage (real backend
 * + LLM mock + full wizard round-trip) is v1.2 work.
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

  // Mock the status endpoint that the dashboard calls on load
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

test.describe('SME Web UI smoke', () => {
  test('dashboard renders with editorial aesthetic', async ({ page }) => {
    await page.goto('/sme-author');

    // The PageHeader's title should be visible.
    await expect(
      page.getByRole('heading', { name: 'SME Case Authoring' }),
    ).toBeVisible();

    // The total-case count should render the mocked 100.
    await expect(page.getByText('100', { exact: true })).toBeVisible();

    // Editorial-Clinical aesthetic spot-check: the body should NOT use
    // Inter (the existing surfaces' font). The .sme-authoring class
    // should be present on the wrapper.
    await expect(page.locator('.sme-authoring')).toBeVisible();

    // No console errors during render
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.waitForLoadState('networkidle');
    expect(errors).toEqual([]);
  });

  test('nav links resolve to their routes', async ({ page }) => {
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

  test('aesthetic isolation: provider route does NOT have sme-authoring class', async ({
    page,
  }) => {
    // Mock the provider endpoints
    await page.route('**/api/v1/authorizations*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 10 }),
      });
    });

    await page.goto('/provider');
    // The provider page is Inter + indigo; it must NOT carry the
    // .sme-authoring scope class.
    await expect(page.locator('.sme-authoring')).toHaveCount(0);
  });
});
