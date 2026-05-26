/**
 * Drafting / validation / commit hooks for the new-case wizard.
 *
 *   useDraft        — POST /sessions/{id}/draft (REST, buffered)
 *   useValidate     — POST /sessions/{id}/validate (with optional draft override)
 *   useCommit       — POST /sessions/{id}/commit (with attestation)
 *   useWebSocketDraft — live token streaming via WS /draft-stream
 *
 * The WebSocket hook is the load-bearing piece: browsers can't set
 * custom headers on WebSocket connections, so we follow the backend's
 * first-message auth protocol — open the socket, then immediately send
 * {type: 'auth', token: '...'} before any other traffic.
 *
 * Reconnect policy: NONE in v1.1. If the WS drops mid-draft, the UI
 * falls back to the REST draft endpoint (also exposed here as
 * useDraft). The session's `draft` is the same regardless of path.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { smeApi } from '../api';
import type {
  CaseDraftResponse,
  CommitRequest,
  CommitResponse,
  DraftResponse,
  ValidateRequest,
  ValidateResponse,
  WSEvent,
} from '../types';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function initial<T>(): AsyncState<T> {
  return { data: null, loading: false, error: null };
}

// =============================================================================
// REST drafting (buffered)
// =============================================================================

export function useDraft() {
  const [state, setState] = useState<AsyncState<DraftResponse>>(initial);

  const run = useCallback(async (sessionId: string) => {
    setState({ data: null, loading: true, error: null });
    try {
      const data = await smeApi.draft(sessionId);
      setState({ data, loading: false, error: null });
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Drafting failed';
      setState({ data: null, loading: false, error: message });
      throw err;
    }
  }, []);

  return { ...state, run };
}

export function useValidate() {
  const [state, setState] = useState<AsyncState<ValidateResponse>>(initial);

  const run = useCallback(
    async (sessionId: string, body: ValidateRequest = {}) => {
      setState({ data: null, loading: true, error: null });
      try {
        const data = await smeApi.validate(sessionId, body);
        setState({ data, loading: false, error: null });
        return data;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Validation failed';
        setState({ data: null, loading: false, error: message });
        throw err;
      }
    },
    [],
  );

  return { ...state, run };
}

export function useCommit() {
  const [state, setState] = useState<AsyncState<CommitResponse>>(initial);

  const run = useCallback(async (sessionId: string, body: CommitRequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const data = await smeApi.commit(sessionId, body);
      setState({ data, loading: false, error: null });
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Commit failed';
      setState({ data: null, loading: false, error: message });
      throw err;
    }
  }, []);

  return { ...state, run };
}

// =============================================================================
// WebSocket streaming
// =============================================================================

export type WSDraftStatus =
  | 'idle'
  | 'connecting'
  | 'authenticating'
  | 'drafting'
  | 'done'
  | 'error';

export interface UseWebSocketDraftState {
  status: WSDraftStatus;
  /** Accumulated text per-field, e.g. {clinical_notes: "65yo male..."}. */
  deltas: Record<string, string>;
  /** Final draft once the 'done' event arrives. */
  draft: CaseDraftResponse | null;
  allocatedCaseId: string | null;
  recommendedFile: string | null;
  error: string | null;
}

interface UseWebSocketDraftOptions {
  /** Called when the 'done' event arrives. */
  onDone?: (draft: CaseDraftResponse) => void;
  /** Called when an 'error' event arrives OR the socket closes unexpectedly. */
  onError?: (message: string) => void;
}

/**
 * Subscribe to the live drafting stream.
 *
 * Usage:
 *   const ws = useWebSocketDraft({ onDone, onError });
 *   ws.connect(sessionId);
 *   // later: ws.disconnect()
 *
 * The hook handles:
 *   1. Opening the WebSocket
 *   2. Sending the first-message auth {type:"auth", token:"<JWT>"}
 *   3. Consuming delta / done / error / heartbeat events
 *   4. Accumulating per-field deltas for typewriter rendering
 *   5. Cleaning up on unmount or explicit disconnect
 */
export function useWebSocketDraft(options: UseWebSocketDraftOptions = {}) {
  const [state, setState] = useState<UseWebSocketDraftState>({
    status: 'idle',
    deltas: {},
    draft: null,
    allocatedCaseId: null,
    recommendedFile: null,
    error: null,
  });

  // Stable refs so the cleanup effect doesn't tear down a fresh socket
  const socketRef = useRef<WebSocket | null>(null);
  const onDoneRef = useRef(options.onDone);
  const onErrorRef = useRef(options.onError);

  useEffect(() => {
    onDoneRef.current = options.onDone;
    onErrorRef.current = options.onError;
  }, [options.onDone, options.onError]);

  const disconnect = useCallback(() => {
    const sock = socketRef.current;
    if (sock && sock.readyState !== WebSocket.CLOSED) {
      sock.close(1000, 'client disconnect');
    }
    socketRef.current = null;
  }, []);

  const connect = useCallback(
    (sessionId: string) => {
      // Tear down any previous socket
      disconnect();

      const token = localStorage.getItem('token');
      if (!token) {
        const msg = 'No auth token in localStorage; cannot open drafting socket.';
        setState((s) => ({ ...s, status: 'error', error: msg }));
        onErrorRef.current?.(msg);
        return;
      }

      setState({
        status: 'connecting',
        deltas: {},
        draft: null,
        allocatedCaseId: null,
        recommendedFile: null,
        error: null,
      });

      const url = smeApi.draftStreamUrl(sessionId);
      const sock = new WebSocket(url);
      socketRef.current = sock;

      sock.onopen = () => {
        // First-message auth — backend rejects any other event before
        // the auth handshake completes.
        setState((s) => ({ ...s, status: 'authenticating' }));
        sock.send(JSON.stringify({ type: 'auth', token }));
        // Backend transitions to drafting after auth-ok. We move the
        // client's status forward when we see the first delta or done
        // event (server-driven) — until then we stay in 'authenticating'.
      };

      sock.onmessage = (msgEvent) => {
        let event: WSEvent;
        try {
          event = JSON.parse(msgEvent.data) as WSEvent;
        } catch {
          // Ignore malformed frames — the backend never sends non-JSON
          return;
        }

        switch (event.type) {
          case 'delta':
            setState((s) => ({
              ...s,
              status: 'drafting',
              deltas: {
                ...s.deltas,
                [event.field]: (s.deltas[event.field] ?? '') + event.content,
              },
            }));
            break;
          case 'done':
            setState((s) => ({
              ...s,
              status: 'done',
              draft: event.draft,
              allocatedCaseId: event.allocated_case_id,
              recommendedFile: event.recommended_file,
            }));
            onDoneRef.current?.(event.draft);
            // Server typically closes after 'done'; close defensively
            sock.close(1000, 'done received');
            break;
          case 'error':
            setState((s) => ({
              ...s,
              status: 'error',
              error: event.message,
            }));
            onErrorRef.current?.(event.message);
            sock.close(1000, 'error received');
            break;
          case 'heartbeat':
            // No state change; just keeps the connection alive
            break;
        }
      };

      sock.onerror = () => {
        // The browser's WebSocket error is opaque (no detail leaked
        // for security). We surface a generic message.
        const msg = 'WebSocket connection error';
        setState((s) => ({ ...s, status: 'error', error: msg }));
        onErrorRef.current?.(msg);
      };

      sock.onclose = (closeEvent) => {
        // Only mark error if we didn't already reach 'done' or surface
        // a server-sent error
        setState((s) => {
          if (s.status === 'done' || s.status === 'error') return s;
          const msg = `WebSocket closed unexpectedly (code ${closeEvent.code})`;
          onErrorRef.current?.(msg);
          return { ...s, status: 'error', error: msg };
        });
      };
    },
    [disconnect],
  );

  // Clean up on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { ...state, connect, disconnect };
}
