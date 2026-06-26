import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@tradeflow/ui';
import Link from 'next/link';

import { fetchLiveness, HealthStatusCard } from '@/features/health';
import { getPublicApiDocsUrl } from '@/lib/api';
import { ApiClientError } from '@/lib/errors';
import { logger } from '@/lib/logging';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  let health = null;
  let healthError: string | null = null;

  try {
    health = await fetchLiveness();
  } catch (error) {
    healthError =
      error instanceof ApiClientError
        ? `${error.code}: ${error.message}`
        : 'Unable to reach API';
    logger.warn('homepage_health_check_failed', { error: healthError });
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-8 px-6 py-16">
      <section className="space-y-4">
        <p className="text-sm font-medium uppercase tracking-wider text-primary">TradeFlow AI</p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Multi-account trade execution platform
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          Professional cloud-based trade copier, risk management, and trading analytics — built for
          serious futures and prop firm traders.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link href={getPublicApiDocsUrl()} target="_blank" rel="noopener noreferrer">
              API Documentation
            </Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        {health ? (
          <HealthStatusCard health={health} />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>API Status</CardTitle>
              <CardDescription>Backend liveness probe</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-destructive">{healthError ?? 'Unavailable'}</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Foundation</CardTitle>
            <CardDescription>Enterprise-grade monorepo scaffold</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>Next.js 15 · FastAPI · PostgreSQL · Redis · Celery</p>
            <p>Structured logging · Centralized errors · DI · API versioning</p>
            <p>Feature-based architecture · Docker · CI/CD</p>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
