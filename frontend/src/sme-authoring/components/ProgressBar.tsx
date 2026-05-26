/**
 * Editorial hairline progress bar.
 *
 * A thin filled rule over a softer base rule — quieter than a Material
 * progress component, but visually unmistakable. Used by BatchList /
 * GapList / DatasetStatus to show counts vs. targets.
 */

interface ProgressBarProps {
  current: number;
  target: number;
  /** Tone of the fill — defaults to deep ink. */
  tone?: 'ink' | 'approve' | 'review' | 'deny';
  /** Optional max-width; defaults to 100% of parent. */
  width?: string;
}

const TONE_VAR: Record<NonNullable<ProgressBarProps['tone']>, string> = {
  ink: 'var(--sme-deep-ink)',
  approve: 'var(--sme-approve)',
  review: 'var(--sme-review)',
  deny: 'var(--sme-deny)',
};

export function ProgressBar({
  current,
  target,
  tone = 'ink',
  width = '100%',
}: ProgressBarProps) {
  const ratio =
    target <= 0 ? 0 : Math.max(0, Math.min(1, current / target));
  return (
    <div
      role="progressbar"
      aria-valuenow={current}
      aria-valuemin={0}
      aria-valuemax={target}
      style={{
        width,
        height: '4px',
        backgroundColor: 'var(--sme-rule-soft)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          width: `${ratio * 100}%`,
          height: '100%',
          backgroundColor: TONE_VAR[tone],
          transition: 'width var(--sme-transition-slow)',
        }}
      />
    </div>
  );
}
