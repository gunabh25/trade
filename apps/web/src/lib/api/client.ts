import type { ApiResponse } from '@tradeflow/types/api';

import { ApiClientError, isApiErrorResponse } from '@/lib/errors';
import { logger } from '@/lib/logging';

const DEFAULT_TIMEOUT_MS = 10_000;
const BUILD_PLACEHOLDER_API_URL = 'http://127.0.0.1:8000';

function resolveServerApiBaseUrl(): string | undefined {
  const candidates = [
    process.env.API_PROXY_URL,
    process.env.NEXT_PUBLIC_API_URL,
    process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : undefined,
  ];

  for (const candidate of candidates) {
    if (!candidate) {
      continue;
    }
    const normalized = candidate.replace(/\/$/, '');
    if (
      normalized === BUILD_PLACEHOLDER_API_URL ||
      normalized.includes('${{') ||
      normalized.includes('RAILWAY_PUBLIC_DOMAIN')
    ) {
      continue;
    }
    return normalized;
  }

  if (process.env.NEXT_PHASE === 'phase-production-build') {
    return BUILD_PLACEHOLDER_API_URL;
  }

  return undefined;
}

/** Base URL for API requests (no trailing slash). Browser production uses same-origin proxy. */
export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
    return '';
  }

  const baseUrl = resolveServerApiBaseUrl();
  if (!baseUrl) {
    throw new Error('NEXT_PUBLIC_API_URL or API_PROXY_URL is not configured');
  }
  return baseUrl;
}

export function getApiVersion(): string {
  return process.env.NEXT_PUBLIC_API_VERSION ?? 'v1';
}

export function buildApiUrl(path: string): string {
  return `${getApiBaseUrl()}/api/${getApiVersion()}${path}`;
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  timeoutMs?: number;
  csrfToken?: string;
  /** Skip warn-level logging for expected failures (e.g. unauthenticated /auth/me). */
  silent?: boolean;
}

function getCsrfToken(): string | undefined {
  if (typeof document === 'undefined') {
    return undefined;
  }
  const match = /(?:^|; )tf_csrf=([^;]*)/.exec(document.cookie);
  return match?.[1] ? decodeURIComponent(match[1]) : undefined;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const { body, timeoutMs = DEFAULT_TIMEOUT_MS, headers, csrfToken, silent, ...rest } = options;
  const url = buildApiUrl(path);

  const controller = new AbortController();
  const timeout = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  const requestHeaders = new Headers(headers);
  requestHeaders.set('Accept', 'application/json');
  if (body !== undefined) {
    requestHeaders.set('Content-Type', 'application/json');
  }

  const csrf = csrfToken ?? getCsrfToken();
  if (csrf && rest.method && rest.method !== 'GET') {
    requestHeaders.set('X-CSRF-Token', csrf);
  }

  try {
    const init: RequestInit = {
      ...rest,
      headers: requestHeaders,
      signal: controller.signal,
      cache: 'no-store',
      credentials: 'include',
    };

    if (body !== undefined) {
      init.body = JSON.stringify(body);
    }

    const response = await fetch(url, init);

    const responseBody: unknown = await response.json().catch(() => null);

    if (!response.ok) {
      if (isApiErrorResponse(responseBody)) {
        throw new ApiClientError(response.status, responseBody);
      }
      throw new ApiClientError(response.status, {
        error: {
          code: 'INTERNAL_ERROR',
          message: `Request failed with status ${String(response.status)}`,
        },
      });
    }

    if (
      !responseBody ||
      typeof responseBody !== 'object' ||
      !('data' in (responseBody as Record<string, unknown>))
    ) {
      throw new ApiClientError(response.status, {
        error: {
          code: 'INTERNAL_ERROR',
          message: 'API returned an invalid response body',
        },
      });
    }

    return responseBody as ApiResponse<T>;
  } catch (error) {
    if (error instanceof ApiClientError) {
      if (!(silent && error.status === 401)) {
        logger.warn('api_request_failed', {
          path,
          code: error.code,
          status: error.status,
          requestId: error.requestId,
        });
      }
      throw error;
    }

    logger.error('api_request_error', {
      path,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

/** Direct API host for assets/docs when the browser uses the same-origin proxy. */
export function getApiAssetBaseUrl(): string {
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
    const upstream = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '');
    if (upstream && upstream !== BUILD_PLACEHOLDER_API_URL && !upstream.includes('${{')) {
      return upstream;
    }
    return window.location.origin;
  }
  return getApiBaseUrl();
}

export function getPublicApiDocsUrl(): string {
  return `${getApiAssetBaseUrl()}/api/docs`;
}

export function getOAuthUrl(provider: 'google' | 'github'): string {
  return buildApiUrl(`/auth/oauth/${provider}`);
}
