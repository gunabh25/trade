import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'content-length',
  'host',
  'keep-alive',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
]);

function stripSetCookieDomain(value: string): string {
  return value
    .split(/;\s*/)
    .filter((part) => !part.toLowerCase().startsWith('domain='))
    .join('; ');
}

export function getUpstreamApiBase(): string | null {
  const candidates = [
    process.env.API_PROXY_URL,
    process.env.INTERNAL_API_URL,
    process.env.NEXT_PUBLIC_API_URL,
  ];

  for (const candidate of candidates) {
    if (!candidate) {
      continue;
    }
    const normalized = candidate.replace(/\/$/, '');
    if (normalized.includes('${{') || normalized.includes('RAILWAY_PUBLIC_DOMAIN')) {
      continue;
    }
    try {
      const parsed = new URL(normalized.startsWith('http') ? normalized : `https://${normalized}`);
      if (!parsed.hostname.includes('.')) {
        continue;
      }
      return `${parsed.protocol}//${parsed.host}`;
    } catch {
      continue;
    }
  }

  return null;
}

export async function proxyToBackend(
  request: NextRequest,
  pathSegments: string[],
): Promise<NextResponse> {
  const upstream = getUpstreamApiBase();
  if (!upstream) {
    return NextResponse.json(
      {
        error: {
          code: 'API_PROXY_NOT_CONFIGURED',
          message:
            'API proxy is not configured. Set API_PROXY_URL on the web service to your API public URL.',
        },
      },
      { status: 502 },
    );
  }

  const path = pathSegments.join('/');
  const target = `${upstream}/api/v1/${path}${request.nextUrl.search}`;

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lower)) {
      return;
    }
    headers.set(key, value);
  });

  const method = request.method.toUpperCase();
  const hasBody = method !== 'GET' && method !== 'HEAD';
  const body = hasBody ? await request.arrayBuffer() : null;

  const upstreamResponse = await fetch(target, {
    method,
    headers,
    body,
    redirect: 'manual',
    cache: 'no-store',
  });

  const responseHeaders = new Headers();
  upstreamResponse.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lower)) {
      return;
    }
    if (lower === 'set-cookie') {
      responseHeaders.append(key, stripSetCookieDomain(value));
      return;
    }
    responseHeaders.set(key, value);
  });

  return new NextResponse(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}
