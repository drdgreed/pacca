/**
 * Read-only hooks for the SME-authoring discovery surfaces.
 *
 *   useStatus   — dataset snapshot for the dashboard
 *   useBatches  — DATASET_GROWTH_ROADMAP batch index
 *   useBatch    — single batch detail
 *   useGaps     — prioritized coverage gaps
 *
 * Each hook mirrors the shape used by `frontend/src/hooks/useApi.ts`:
 *   { data, loading, error, fetch }
 *
 * `fetch` is exposed as the imperative trigger (not auto-fetched on mount)
 * so consumers can compose multiple loads under a single loading state.
 * Pages that want auto-load call `fetch()` in a `useEffect`.
 */

import { useCallback, useEffect, useState } from 'react';
import { smeApi } from '../api';
import type {
  BatchListResponse,
  BatchResponse,
  GapListResponse,
  StatusResponse,
} from '../types';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function initial<T>(): AsyncState<T> {
  return { data: null, loading: false, error: null };
}

export function useStatus(autoFetch = true) {
  const [state, setState] = useState<AsyncState<StatusResponse>>(initial);

  const fetch = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await smeApi.status();
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load status',
      });
    }
  }, []);

  useEffect(() => {
    if (autoFetch) void fetch();
  }, [autoFetch, fetch]);

  return { ...state, fetch };
}

export function useBatches(autoFetch = true) {
  const [state, setState] = useState<AsyncState<BatchListResponse>>(initial);

  const fetch = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await smeApi.listBatches();
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load batches',
      });
    }
  }, []);

  useEffect(() => {
    if (autoFetch) void fetch();
  }, [autoFetch, fetch]);

  return { ...state, fetch };
}

export function useBatch(batchId: string | null, autoFetch = true) {
  const [state, setState] = useState<AsyncState<BatchResponse>>(initial);

  const fetch = useCallback(async () => {
    if (!batchId) return;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await smeApi.getBatch(batchId);
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load batch',
      });
    }
  }, [batchId]);

  useEffect(() => {
    if (autoFetch && batchId) void fetch();
  }, [autoFetch, batchId, fetch]);

  return { ...state, fetch };
}

export function useGaps(autoFetch = true) {
  const [state, setState] = useState<AsyncState<GapListResponse>>(initial);

  const fetch = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await smeApi.listGaps();
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load gaps',
      });
    }
  }, []);

  useEffect(() => {
    if (autoFetch) void fetch();
  }, [autoFetch, fetch]);

  return { ...state, fetch };
}
