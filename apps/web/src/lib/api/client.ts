import type { ApiResponse } from '@tradeflow/types/api';

import { ApiClientError, isApiErrorResponse } from '@/lib/errors';
import { logger } from '@/lib/logging';

const DEFAULT_TIMEOUT_MS = 10_000;

function getApiBaseUrl(): string {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_URL ??
    (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : undefined);
  if (!baseUrl) {
    throw new Error('NEXT_PUBLIC_API_URL is not configured');
  }
  return baseUrl.replace(/\/$/, '');
}

function getApiVersion(): string {
  return process.env.NEXT_PUBLIC_API_VERSION ?? 'v1';
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
  const url = `${getApiBaseUrl()}/api/${getApiVersion()}${path}`;

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

export function getPublicApiDocsUrl(): string {
  return `${getApiBaseUrl()}/api/docs`;
}

export function getOAuthUrl(provider: 'google' | 'github'): string {
  return `${getApiBaseUrl()}/api/${getApiVersion()}/auth/oauth/${provider}`;
}
