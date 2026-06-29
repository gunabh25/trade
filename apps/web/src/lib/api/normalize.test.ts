import { describe, expect, it, vi } from 'vitest';

import {
  formatRelativeTime,
  toNullableNumber,
  toNullableString,
  toNumber,
  toString,
  toStringArray,
} from './normalize';

describe('normalize utilities', () => {
  it('toNumber converts valid values and uses fallback', () => {
    expect(toNumber('42')).toBe(42);
    expect(toNumber(null)).toBe(0);
    expect(toNumber('not-a-number', 7)).toBe(7);
  });

  it('toNullableNumber returns null for invalid input', () => {
    expect(toNullableNumber('12.5')).toBe(12.5);
    expect(toNullableNumber('')).toBeNull();
    expect(toNullableNumber(undefined)).toBeNull();
  });

  it('toString and toNullableString handle scalars', () => {
    expect(toString(99)).toBe('99');
    expect(toString(null, 'fallback')).toBe('fallback');
    expect(toNullableString(true)).toBe('true');
    expect(toNullableString({})).toBeNull();
  });

  it('toStringArray maps arrays or returns null', () => {
    expect(toStringArray(['a', 1])).toEqual(['a', '1']);
    expect(toStringArray('nope')).toBeNull();
  });

  it('formatRelativeTime handles empty and recent timestamps', () => {
    expect(formatRelativeTime(null)).toBe('Never');
    expect(formatRelativeTime(new Date(Date.now() - 30_000).toISOString())).toBe('Just now');
  });

  it('toNullableString returns null for objects', () => {
    expect(toNullableString({})).toBeNull();
  });

  it('formatRelativeTime handles future timestamps', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-26T12:00:00Z'));
    expect(formatRelativeTime('2026-06-27T12:00:00Z')).toBe('Just now');
    vi.useRealTimers();
  });

  it('formatRelativeTime handles minutes, hours, and days', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-26T12:00:00Z'));

    expect(formatRelativeTime('2026-06-26T11:30:00Z')).toBe('30m ago');
    expect(formatRelativeTime('2026-06-26T09:00:00Z')).toBe('3h ago');
    expect(formatRelativeTime('2026-06-24T12:00:00Z')).toBe('2d ago');

    vi.useRealTimers();
  });
});
