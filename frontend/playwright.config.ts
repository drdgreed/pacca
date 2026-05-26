/**
 * Playwright config — SME Case Authoring Web UI E2E.
 *
 * Smoke-test the happy path only in v1.1. Wider E2E coverage
 * (negative paths, accessibility audits) is v1.2.
 *
 * Before first use:
 *   cd frontend && npx playwright install --with-deps chromium
 *
 * Then run:
 *   cd frontend && npx playwright test
 *   (or:  make sme-author-web-e2e — wired in Makefile)
 *
 * The webServer block boots Vite on demand so tests have a live
 * frontend to drive. The backend is NOT auto-started — set up your
 * mock or live API separately. For pure-frontend smoke tests against
 * mocked fetch responses, see e2e/smoke.spec.ts.
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
