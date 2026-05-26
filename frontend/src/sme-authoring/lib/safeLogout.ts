/**
 * Safe logout — clears the JWT and scrubs any PHI-shaped keys from
 * browser storage.
 *
 * The SME-authoring surface stores ONLY the auth token in localStorage
 * by design. This helper enforces that contract at logout: any unexpected
 * key that contains a PHI-pattern in its name or value is removed and
 * (in development) logged to the console with a one-line warning so the
 * developer can find where the leak originated.
 *
 * The contract is paranoid by intent — even though the wizard keeps its
 * state purely in React useReducer (never persists to storage), the
 * logout-time check is the safety net against future regressions that
 * accidentally call localStorage.setItem with case content.
 */

import { scanForPhiClient } from '../wizard/phiClientScan';

/** Keys that ARE expected to live in localStorage. Everything else is suspect. */
const EXPECTED_KEYS = new Set([
  'token',
  // React Router doesn't persist by default; Vite HMR uses sessionStorage
]);

interface SafeLogoutReport {
  cleared: string[];
  /** Keys whose contents matched a PHI pattern. */
  phiFlagged: string[];
}

/**
 * Clear the JWT and any unexpected localStorage entries.
 *
 * Returns a report of what was cleared (for telemetry / dev console).
 * The report itself never contains PHI — only the KEY names, which by
 * the SME-authoring contract are themselves PHI-free.
 */
export function safeLogout(): SafeLogoutReport {
  const cleared: string[] = [];
  const phiFlagged: string[] = [];

  // Snapshot keys before mutating — localStorage indices shift on remove.
  const keys: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k) keys.push(k);
  }

  for (const key of keys) {
    if (EXPECTED_KEYS.has(key)) {
      // Expected — clear unconditionally (logout removes the JWT)
      localStorage.removeItem(key);
      cleared.push(key);
      continue;
    }
    // Unexpected key. Inspect the value for PHI patterns before removal.
    const value = localStorage.getItem(key);
    if (value && scanForPhiClient(value).length > 0) {
      phiFlagged.push(key);
    }
    localStorage.removeItem(key);
    cleared.push(key);
  }

  // Dev-only diagnostic — production builds elide via Vite's import.meta.env.DEV
  if (
    typeof window !== 'undefined' &&
    (import.meta as ImportMeta & { env?: { DEV?: boolean } }).env?.DEV &&
    phiFlagged.length > 0
  ) {
    // eslint-disable-next-line no-console
    console.warn(
      `[safeLogout] PHI-shaped content found in localStorage keys: ${phiFlagged.join(', ')}. ` +
        'These keys were cleared. Investigate whether the wizard or a component is ' +
        'persisting case content — it should not.',
    );
  }

  return { cleared, phiFlagged };
}
