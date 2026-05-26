/**
 * Editorial step indicator — 6 hairline segments, the active one inked.
 *
 * Replaces the cliched progress bar / circular-step UI with the
 * editorial-clinical equivalent of a manuscript page-mark.
 */

import { STEP_LABELS } from './wizardState';
import type { WizardStep } from './wizardState';

interface StepIndicatorProps {
  current: WizardStep;
  onJump?: (step: WizardStep) => void;
  /** Steps the user has already completed (can be revisited). */
  visited: Set<Exclude<WizardStep, 'done'>>;
}

const STEPS: Exclude<WizardStep, 'done'>[] = [1, 2, 3, 4, 5, 6];

export function StepIndicator({ current, visited, onJump }: StepIndicatorProps) {
  return (
    <nav
      aria-label="Wizard progress"
      style={{
        display: 'flex',
        gap: '0.5rem',
        marginBottom: '2.5rem',
      }}
    >
      {STEPS.map((step) => {
        const isCurrent = step === current;
        const isVisited = visited.has(step);
        const clickable = isVisited && !isCurrent && Boolean(onJump);
        return (
          <button
            key={step}
            type="button"
            disabled={!clickable}
            onClick={() => clickable && onJump?.(step)}
            style={{
              flex: 1,
              background: 'none',
              border: 'none',
              padding: '0.5rem 0',
              textAlign: 'left',
              cursor: clickable ? 'pointer' : 'default',
              borderTop: `2px solid ${
                isCurrent
                  ? 'var(--sme-deep-ink)'
                  : isVisited
                    ? 'var(--sme-rule)'
                    : 'var(--sme-rule-soft)'
              }`,
              opacity: isCurrent || isVisited ? 1 : 0.6,
              transition: 'opacity var(--sme-transition)',
            }}
          >
            <div
              className="sme-mono"
              style={{
                fontSize: '0.6875rem',
                color: 'var(--sme-muted)',
                marginTop: '0.25rem',
              }}
            >
              {String(step).padStart(2, '0')}
            </div>
            <div
              style={{
                fontVariant: 'small-caps',
                letterSpacing: '0.06em',
                fontSize: '0.8125rem',
                marginTop: '0.125rem',
                color: isCurrent ? 'var(--sme-deep-ink)' : 'var(--sme-muted)',
                fontWeight: isCurrent ? 600 : 400,
              }}
            >
              {STEP_LABELS[step]}
            </div>
          </button>
        );
      })}
    </nav>
  );
}
