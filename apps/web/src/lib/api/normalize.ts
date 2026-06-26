/** Normalize API scalar values (Decimal, UUID, dates) for UI consumption. */

export function toNumber(value: unknown, fallback = 0): number {
  if (value == null || value === '') {
    return fallback;
  }
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function toNullableNumber(value: unknown): number | null {
  if (value == null || value === '') {
    return null;
  }
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function toString(value: unknown, fallback = ''): string {
  if (value == null) {
    return fallback;
  }
  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean' ||
    typeof value === 'bigint'
  ) {
    return String(value);
  }
  return fallback;
}

export function toNullableString(value: unknown): string | null {
  if (value == null) {
    return null;
  }
  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean' ||
    typeof value === 'bigint'
  ) {
    return String(value);
  }
  return null;
}

export function toStringArray(value: unknown): string[] | null {
  if (!Array.isArray(value)) {
    return null;
  }
  return value.map(String);
}

export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) {
    return 'Never';
  }
  const diffMs = Date.now() - new Date(iso).getTime();
  if (diffMs < 0) {
    return 'Just now';
  }
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 1) {
    return 'Just now';
  }
  if (minutes < 60) {
    return `${String(minutes)}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${String(hours)}h ago`;
  }
  const days = Math.floor(hours / 24);
  return `${String(days)}d ago`;
}
