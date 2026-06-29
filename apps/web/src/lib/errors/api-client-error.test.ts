import { describe, expect, it } from 'vitest';

import { ApiClientError, isApiErrorResponse } from './api-client-error';

describe('ApiClientError', () => {
  it('maps API error payload to typed fields', () => {
    const error = new ApiClientError(422, {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid payload',
        requestId: 'req-123',
        details: { field: 'email' },
      },
    });

    expect(error.name).toBe('ApiClientError');
    expect(error.status).toBe(422);
    expect(error.code).toBe('VALIDATION_ERROR');
    expect(error.message).toBe('Invalid payload');
    expect(error.requestId).toBe('req-123');
    expect(error.details).toEqual({ field: 'email' });
  });
});

describe('isApiErrorResponse', () => {
  it('returns true for valid error envelopes', () => {
    expect(
      isApiErrorResponse({
        error: { code: 'UNAUTHORIZED', message: 'Login required' },
      }),
    ).toBe(true);
  });

  it('returns false for invalid shapes', () => {
    expect(isApiErrorResponse(null)).toBe(false);
    expect(isApiErrorResponse({ error: { code: 1 } })).toBe(false);
  });
});
