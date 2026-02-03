import { useState, useCallback } from 'react';
import type {
  Authorization,
  AuthorizationListResponse,
  AuthorizationSubmission,
  ExplanationResponse,
  HealthResponse,
  HumanReviewInput,
  MetricsResponse,
} from '../types';

const API_BASE = '/api/v1';

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// Hook for fetching authorization list
export function useAuthorizations() {
  const [data, setData] = useState<AuthorizationListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (page = 1, status?: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: String(page) });
      if (status) params.append('status', status);
      
      const result = await apiFetch<AuthorizationListResponse>(
        `${API_BASE}/authorizations?${params}`
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetch };
}

// Hook for fetching single authorization
export function useAuthorization(requestId: string | null) {
  const [data, setData] = useState<Authorization | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!requestId) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<Authorization>(
        `${API_BASE}/authorizations/${requestId}`
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  }, [requestId]);

  return { data, loading, error, fetch };
}

// Hook for submitting authorization
export function useSubmitAuthorization() {
  const [data, setData] = useState<Authorization | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (submission: AuthorizationSubmission) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<Authorization>(
        `${API_BASE}/authorizations`,
        {
          method: 'POST',
          body: JSON.stringify(submission),
        }
      );
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Submission failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, submit };
}

// Hook for fetching decision explanation
export function useExplanation(requestId: string | null) {
  const [data, setData] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!requestId) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<ExplanationResponse>(
        `${API_BASE}/authorizations/${requestId}/explain`
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  }, [requestId]);

  return { data, loading, error, fetch };
}

// Hook for submitting human review
export function useHumanReview() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitReview = useCallback(
    async (requestId: string, review: HumanReviewInput) => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFetch<Authorization>(
          `${API_BASE}/authorizations/${requestId}/review`,
          {
            method: 'POST',
            body: JSON.stringify(review),
          }
        );
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Review failed';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { loading, error, submitReview };
}

// Hook for health check
export function useHealth() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const result = await apiFetch<HealthResponse>('/health');
      setData(result);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, fetch };
}

// Hook for metrics
export function useMetrics() {
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const result = await apiFetch<MetricsResponse>(`${API_BASE}/metrics`);
      setData(result);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, fetch };
}
