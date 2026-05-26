/**
 * Client-side PHI pattern scan.
 *
 * Lightweight mirror of the backend's `scan_for_phi()` in
 * src/pacca/agents/sme_authoring/validators.py — runs BEFORE the SME's
 * scenario is transmitted to the server, so the SME sees a warning the
 * instant they paste real patient data into the textarea.
 *
 * IMPORTANT: this is a warning surface, not a security boundary.
 * Defense-in-depth — the backend validator runs the canonical scan;
 * the pre-commit hook runs it again at commit time. This client-side
 * scan is purely UX: catch the obvious mistake before the network hop.
 *
 * The patterns intentionally err toward false-positives — the cost of
 * a needless warning is low (SME confirms and continues); the cost of
 * a missed PHI leak is high.
 */

interface PHIPattern {
  label: string;
  regex: RegExp;
}

const PATTERNS: PHIPattern[] = [
  { label: 'SSN pattern (NNN-NN-NNNN)', regex: /\b\d{3}-\d{2}-\d{4}\b/ },
  { label: 'MRN reference', regex: /\bMRN[:\s#]*\d{4,}\b/i },
  {
    label: 'DOB phrasing',
    regex: /\b(DOB|date of birth)[:\s]+\d/i,
  },
  { label: 'email address', regex: /\b[\w.+-]+@[\w-]+\.[\w-]+\b/ },
  { label: 'phone number', regex: /\b\d{3}[.\-\s]\d{3}[.\-\s]\d{4}\b/ },
  {
    label: 'specific date (M/D/YYYY format)',
    regex: /\b(\d{1,2})\/(\d{1,2})\/(19|20)\d{2}\b/,
  },
  {
    label: 'titled full name (Mr/Mrs/Ms/Dr/Patient + First Last)',
    regex: /\b(Mr|Mrs|Ms|Dr|Patient)\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b/,
  },
  {
    label: 'street address',
    regex:
      /\b\d+\s+([A-Z][a-z]+\s+){1,3}(Street|St|Avenue|Ave|Road|Rd|Blvd|Lane|Ln|Drive|Dr)\b/,
  },
];

export function scanForPhiClient(text: string): string[] {
  const hits: string[] = [];
  for (const p of PATTERNS) {
    if (p.regex.test(text)) {
      hits.push(p.label);
    }
  }
  return hits;
}
