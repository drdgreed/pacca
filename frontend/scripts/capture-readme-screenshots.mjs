#!/usr/bin/env node
/**
 * Capture README screenshots from the running PACCA dev server.
 *
 * Boots a headless Chromium, signs in with a synthetic test user,
 * navigates to the prettiest surfaces, and writes PNG screenshots to
 * docs/images/. Run from the repo root:
 *
 *   cd frontend && node scripts/capture-readme-screenshots.mjs
 *
 * Prereqs:
 *   - Dev server running at http://localhost:3000
 *   - A user with credentials `screenshot / screenshotpw1234` exists
 *     (the script registers one if missing; failure is tolerated)
 *   - Playwright Chromium installed (handled by `npm run test:e2e:install`)
 */

import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const OUT_DIR = path.join(REPO_ROOT, 'docs', 'images');

const USERNAME = 'screenshot';
const PASSWORD = 'screenshotpw1234';
const BASE = 'http://localhost:3000';
const VIEWPORT = { width: 1440, height: 900 };

async function ensureUser() {
  // Best-effort register; ignore failures (likely "already exists")
  try {
    await fetch('http://localhost:8000/api/v1/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: USERNAME, password: PASSWORD }),
    });
  } catch {
    /* ignore */
  }
}

async function signIn(page) {
  await page.goto(`${BASE}/login`);
  await page.getByLabel('Username').fill(USERNAME);
  await page.getByLabel('Password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  // Wait for the redirect to /provider (no longer on /login)
  await page.waitForURL((url) => !url.pathname.endsWith('/login'), {
    timeout: 5000,
  });
}

async function capture(page, route, filename, opts = {}) {
  await page.goto(`${BASE}${route}`);
  await page.waitForLoadState('networkidle');
  // Give web fonts a moment to settle so Source Serif renders, not fallback
  await page.waitForTimeout(500);
  const outPath = path.join(OUT_DIR, filename);
  await page.screenshot({
    path: outPath,
    fullPage: opts.fullPage ?? false,
  });
  console.log(`  ✓ ${filename}  (${route})`);
}

async function main() {
  console.log('PACCA README screenshot capture');
  console.log('────────────────────────────────');
  await mkdir(OUT_DIR, { recursive: true });
  await ensureUser();

  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: VIEWPORT });
  const page = await ctx.newPage();

  // Login page first (no auth needed)
  console.log('\n[1/6] Login page (cream paper, Spectral wordmark)');
  await capture(page, '/login', 'screenshot-01-login.png');

  console.log('\n[2/6] Sign in to capture authenticated surfaces');
  await signIn(page);

  console.log('\n[3/6] Provider surface (Editorial-Clinical reskin)');
  await capture(page, '/provider', 'screenshot-02-provider.png');

  console.log('\n[4/6] SME Authoring Dashboard');
  await capture(page, '/sme-author', 'screenshot-03-sme-dashboard.png');

  console.log('\n[5/6] SME New Case Wizard step 1');
  await capture(page, '/sme-author/new', 'screenshot-04-sme-wizard.png');

  console.log('\n[6/6] Dataset Status page');
  await capture(page, '/sme-author/status', 'screenshot-05-sme-status.png', {
    fullPage: true,
  });

  await browser.close();
  console.log('\n✓ All screenshots saved to docs/images/');
}

main().catch((err) => {
  console.error('FAILED:', err);
  process.exit(1);
});
