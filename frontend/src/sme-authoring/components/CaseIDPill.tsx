/**
 * Monospace case-ID display.
 *
 * Case IDs are GC-NNN. Always render them in JetBrains Mono so they
 * stand out as system-allocated identifiers (vs editorial body text).
 * This is one of the load-bearing typographic moves of the
 * Editorial-Clinical aesthetic.
 */

interface CaseIDPillProps {
  id: string;
  /** Optional size override; defaults to inheriting the parent's font-size. */
  size?: 'sm' | 'md' | 'lg';
  /** Optional emphasis: 'ink' = solid, 'muted' = secondary, 'deep' = navy. */
  tone?: 'ink' | 'muted' | 'deep';
}

const SIZE_MAP: Record<NonNullable<CaseIDPillProps['size']>, string> = {
  sm: '0.8rem',
  md: '0.95rem',
  lg: '1.15rem',
};

const TONE_MAP: Record<NonNullable<CaseIDPillProps['tone']>, string> = {
  ink: 'var(--sme-ink)',
  muted: 'var(--sme-muted)',
  deep: 'var(--sme-deep-ink)',
};

export function CaseIDPill({ id, size = 'md', tone = 'deep' }: CaseIDPillProps) {
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
      {id}
    </span>
  );
}
