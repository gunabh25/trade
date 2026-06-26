import type { ApiErrorResponse } from '@tradeflow/types/api';

export class ApiClientError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId?: string;
  readonly details?: ApiErrorResponse['error']['details'];

  constructor(status: number, body: ApiErrorResponse) {
    super(body.error.message);
    this.name = 'ApiClientError';
    this.code = body.error.code;
    this.status = status;
    if (body.error.requestId !== undefined) {
      this.requestId = body.error.requestId;
    }
    if (body.error.details !== undefined) {
      this.details = body.error.details;
    }
  }
}

export function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== 'object' || value === null) return false;
  const record = value as Record<string, unknown>;
  if (typeof record.error !== 'object' || record.error === null) return false;
  const error = record.error as Record<string, unknown>;
  return typeof error.code === 'string' && typeof error.message === 'string';
}
