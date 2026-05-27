/**
 * StatusInk — Editorial-Clinical status indicator.
 *
 * Replaces the legacy Tailwind pattern of filled colored badges
 * (`bg-success-50 text-success-600` etc.) with ink-color status text.
 * Per the Editorial-Clinical aesthetic: status is conveyed via text
 * color + optional left-border accent, not filled pills.
 *
 * Five semantic outcomes covering both authorization workflow states
 * and decisions. Maps onto the four `--sme-*` accent colors.
 *
 * Usage:
 *   <StatusInk outcome="approved">Approved</StatusInk>
 *   <StatusInk outcome="denied" withRule>Denied</StatusInk>
 *   <StatusInk outcome="review">Pending review</StatusInk>
 *
 * The `withRule` prop adds a 2px left border in the same color —
 * useful for row-level status indicators (e.g., authorization-list
 * rows where the status needs slightly more visual weight).
 */

import type { ReactNode } from 'react';

export type StatusOutcome =
  | 'approved'
  | 'denied'
  | 'review'
  | 'info'
  | 'processing';

interface StatusInkProps {
  outcome: StatusOutcome;
  children: ReactNode;
  /** Add a 2px left border in the status color. */
  withRule?: boolean;
  /** Optional inline style override. */
  style?: React.CSSProperties;
}

const OUTCOME_TO_CLASS: Record<StatusOutcome, string> = {
  approved: 'sme-status-approve',
  denied: 'sme-status-deny',
  review: 'sme-status-review',
  info: 'sme-status-info',
  // "processing" reuses the info accent — visually identical because
  // both signal "the system is working on this." If a future design
  // adds a distinct color (e.g., pulse animation), introduce it here.
  processing: 'sme-status-info',
};

const OUTCOME_TO_VAR: Record<StatusOutcome, string> = {
  approved: 'var(--sme-approve)',
  denied: 'var(--sme-deny)',
  review: 'var(--sme-review)',
  info: 'var(--sme-info)',
  processing: 'var(--sme-info)',
};

export function StatusInk({
  outcome,
  children,
  withRule = false,
  style,
}: StatusInkProps) {
  const ruleStyle: React.CSSProperties = withRule
    ? {
        borderLeft: `2px solid ${OUTCOME_TO_VAR[outcome]}`,
        paddingLeft: '0.75rem',
      }
    : {};

  return (
    <span
      className={OUTCOME_TO_CLASS[outcome]}
      style={{
        fontWeight: 600,
        ...ruleStyle,
        ...style,
      }}
    >
      {children}
    </span>
  );
}
