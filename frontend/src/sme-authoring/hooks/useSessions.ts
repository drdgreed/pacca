/**
 * Session-lifecycle hooks for the SME-authoring surface.
 *
 *   useSessions       — list saved sessions (auto-fetches on mount)
 *   useSession        — load one session by id
 *   useCreateSession  — POST /sessions with scenario + mode
 *   useDeleteSession  — DELETE /sessions/{id}
 *
 * Mirrors the imperative pattern in `frontend/src/hooks/useApi.ts`.
 * Mutating hooks (create/delete) return an action function rather than
 * auto-firing on mount.
 */

import { useCallback, useEffect, useState } from 'react';
import { smeApi } from '../api';
import type {
  CreateSessionRequest,
  SessionListResponse,
  SessionResponse,
} from '../types';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function initial<T>(): AsyncState<T> {
  return { data: null, loading: false, error: null };
}

export function useSessions(autoFetch = true) {
  const [state, setState] = useState<AsyncState<SessionListResponse>>(initial);

  const fetch = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await smeApi.listSessions();
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load sessions',
      });
    }
  }, []);

  useEffect(() => {
    if (autoFetch) void fetch();
  }, [autoFetch, fetch]);

  return { ...state, fetch };
}

export function useSession(sessionId: string | null, autoFetch = true) {
  const [state, setState] = useState<AsyncState<SessionResponse>>(initial);

  const fetch = useCallback(async () => {
    if (!sessionId) return;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await smeApi.getSession(sessionId);
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load session',
      });
    }
  }, [sessionId]);

  useEffect(() => {
    if (autoFetch && sessionId) void fetch();
  }, [autoFetch, sessionId, fetch]);

  return { ...state, fetch };
}

export function useCreateSession() {
  const [state, setState] = useState<AsyncState<SessionResponse>>(initial);

  const create = useCallback(async (req: CreateSessionRequest) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await smeApi.createSession(req);
      setState({ data, loading: false, error: null });
      return data;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to create session';
      setState({ data: null, loading: false, error: message });
      throw err;
    }
  }, []);

  return { ...state, create };
}

export function useDeleteSession() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const remove = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      await smeApi.deleteSession(sessionId);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to delete session';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, remove };
}
