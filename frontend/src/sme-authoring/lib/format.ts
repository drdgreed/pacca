/**
 * Shared formatting helpers for the SME-authoring surface.
 *
 * Pure functions. No React, no hooks. Reusable from pages, components,
 * and (future) tests.
 */

/** Format ISO timestamp as "YYYY-MM-DD HH:MM" (monospace-friendly). */
export function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mins = String(d.getMinutes()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd} ${hh}:${mins}`;
  } catch {
    return iso;
  }
}

/** Format relative time as "5m ago" / "2h ago" / "3d ago". */
export function formatRelative(iso: string): string {
  try {
    const d = new Date(iso);
    const now = Date.now();
    const diff = Math.max(0, now - d.getTime());
    const sec = Math.floor(diff / 1000);
    if (sec < 60) return `${sec}s ago`;
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min}m ago`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr}h ago`;
    const day = Math.floor(hr / 24);
    if (day < 30) return `${day}d ago`;
    const mo = Math.floor(day / 30);
    if (mo < 12) return `${mo}mo ago`;
    return `${Math.floor(mo / 12)}y ago`;
  } catch {
    return '';
  }
}

/** Render a progress fraction as "N of M" with optional percent. */
export function formatFraction(current: number, target: number): string {
  if (target === 0) return `${current}`;
  const pct = Math.round((current / target) * 100);
  return `${current} of ${target} (${pct}%)`;
}
