import { getApiAssetBaseUrl } from '@/lib/api/client';

/** Resolve API-relative avatar paths to a browser-loadable URL. */
export function resolveAvatarUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return `${getApiAssetBaseUrl()}${url.startsWith('/') ? url : `/${url}`}`;
}
