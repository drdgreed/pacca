/**
 * SME Case Authoring API client.
 *
 * Thin wrapper over `fetch` that:
 *   1. Prefixes the SME-authoring route base.
 *   2. Adds the JWT `Authorization` header from localStorage.
 *   3. Parses JSON errors into useful messages.
 *
 * Matches the pattern in `frontend/src/hooks/useApi.ts` (apiFetch).
 * Kept separate so the SME surface can evolve independently without
 * cross-pollinating with the Provider/Director surfaces.
 */

import type {
  BatchListResponse,
  BatchResponse,
  CommitRequest,
  CommitResponse,
  CreateSessionRequest,
  DraftResponse,
  GapListResponse,
  SessionListResponse,
  SessionResponse,
  StatusResponse,
  ValidateRequest,
  ValidateResponse,
} from './types';

const SME_API_BASE = '/api/v1/sme-authoring';

function authHeader(): HeadersInit {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function smeFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${SME_API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || body.message || `HTTP ${response.status}`;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  // Some endpoints (DELETE) return no body
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

// =============================================================================
// Status / discovery — read-only endpoints
// =============================================================================

export const smeApi = {
  status(): Promise<StatusResponse> {
    return smeFetch('/status');
  },

  listBatches(): Promise<BatchListResponse> {
    return smeFetch('/batches');
  },

  getBatch(batchId: string): Promise<BatchResponse> {
    return smeFetch(`/batches/${encodeURIComponent(batchId)}`);
  },

  listGaps(): Promise<GapListResponse> {
    return smeFetch('/gaps');
  },

  // ---------------------------------------------------------------------------
  // Sessions — CRUD
  // ---------------------------------------------------------------------------

  listSessions(): Promise<SessionListResponse> {
    return smeFetch('/sessions');
  },

  getSession(sessionId: string): Promise<SessionResponse> {
    return smeFetch(`/sessions/${encodeURIComponent(sessionId)}`);
  },

  createSession(body: CreateSessionRequest): Promise<SessionResponse> {
    return smeFetch('/sessions', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  deleteSession(sessionId: string): Promise<void> {
    return smeFetch(`/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
    });
  },

  // ---------------------------------------------------------------------------
  // Drafting / validation / commit
  // ---------------------------------------------------------------------------

  draft(sessionId: string): Promise<DraftResponse> {
    return smeFetch(`/sessions/${encodeURIComponent(sessionId)}/draft`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  },

  validate(
    sessionId: string,
    body: ValidateRequest = {},
  ): Promise<ValidateResponse> {
    return smeFetch(`/sessions/${encodeURIComponent(sessionId)}/validate`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  commit(sessionId: string, body: CommitRequest): Promise<CommitResponse> {
    return smeFetch(`/sessions/${encodeURIComponent(sessionId)}/commit`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  // ---------------------------------------------------------------------------
  // WebSocket helper — see hooks/useDrafting.ts (PR-WUI-3)
  // ---------------------------------------------------------------------------

  /**
   * Build the WebSocket URL for the live drafting stream.
   *
   * The token isn't included in the URL (logs leak query strings).
   * The client sends a first-message {type: "auth", token: "..."} per the
   * backend's first-message auth protocol.
   */
  draftStreamUrl(sessionId: string): string {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${proto}//${host}${SME_API_BASE}/sessions/${encodeURIComponent(
      sessionId,
    )}/draft-stream`;
  },
};
