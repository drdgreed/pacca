/**
 * Section heading with the small-caps label + hairline rule
 * that defines the Editorial-Clinical typographic rhythm.
 *
 * Use at the top of any pages or major sections:
 *   <PageHeader label="Dashboard" title="SME Case Authoring" />
 *   <PageHeader label="Section" title="Drafting" hint="Step 2 of 6" />
 */

import type { ReactNode } from 'react';

interface PageHeaderProps {
  /** Small-caps label rendered above the title (e.g. "Dashboard", "Section"). */
  label: string;
  /** Display-serif page title (renders in Spectral). */
  title: string;
  /** Optional contextual note rendered in the muted ink. */
  hint?: string;
  /** Optional right-aligned action cluster (buttons, links). */
  actions?: ReactNode;
}

export function PageHeader({ label, title, hint, actions }: PageHeaderProps) {
  return (
    <header style={{ marginBottom: '2.5rem' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: '2rem',
        }}
      >
        <div style={{ flex: 1 }}>
          <div className="sme-label">{label}</div>
          <h1 style={{ marginTop: '0.5rem', marginBottom: 0 }}>{title}</h1>
          {hint && (
            <p
              style={{
                color: 'var(--sme-muted)',
                marginTop: '0.5rem',
                marginBottom: 0,
                fontSize: '0.95rem',
              }}
            >
              {hint}
            </p>
          )}
        </div>
        {actions && <div>{actions}</div>}
      </div>
      <div className="sme-rule" style={{ marginTop: '1.5rem' }} />
    </header>
  );
}
