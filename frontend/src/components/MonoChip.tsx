/**
 * MonoChip — monospace identifier display.
 *
 * Generalization of CaseIDPill (sme-authoring/components/CaseIDPill.tsx)
 * for any kind of system-allocated identifier: request_id, member_id,
 * CPT / ICD codes, NPIs, anything that should read as "system data"
 * vs editorial body text.
 *
 * Usage:
 *   <MonoChip>GC-101</MonoChip>
 *   <MonoChip size="lg" tone="deep">{requestId}</MonoChip>
 *   <MonoChip size="sm" tone="muted">{cptCode}</MonoChip>
 */

import type { ReactNode } from 'react';

interface MonoChipProps {
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg';
  tone?: 'ink' | 'muted' | 'deep';
}

const SIZE_MAP: Record<NonNullable<MonoChipProps['size']>, string> = {
  sm: '0.8rem',
  md: '0.95rem',
  lg: '1.15rem',
};

const TONE_MAP: Record<NonNullable<MonoChipProps['tone']>, string> = {
  ink: 'var(--sme-ink)',
  muted: 'var(--sme-muted)',
  deep: 'var(--sme-deep-ink)',
};

export function MonoChip({
  children,
  size = 'md',
  tone = 'deep',
}: MonoChipProps) {
  return (
    <span
      className="sme-mono"
      style={{
        fontSize: SIZE_MAP[size],
        color: TONE_MAP[tone],
        fontWeight: 500,
        letterSpacing: '0.02em',
      }}
    >
      {children}
    </span>
  );
}
