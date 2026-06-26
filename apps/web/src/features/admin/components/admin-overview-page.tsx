'use client';

import { AlertCircle } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Button, Skeleton } from '@tradeflow/ui';

import { getAdminOverview } from '@/features/admin/api/admin-api';
import { AdminPageHeader, StatCard } from '@/features/admin/components/admin-ui';
import { EmptyState, FadeInStagger } from '@/features/dashboard/components/motion-primitives';

export function AdminOverviewPage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof getAdminOverview>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await getAdminOverview());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load overview');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="space-y-4 p-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <EmptyState
          icon={AlertCircle}
          title="Admin overview unavailable"
          description={error ?? ''}
          action={
            <Button size="sm" onClick={() => void load()}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div>
      <AdminPageHeader title="Overview" description="Platform metrics and operational snapshot." />
      <FadeInStagger className="grid gap-4 p-4 sm:grid-cols-2 sm:p-6 xl:grid-cols-4">
        <StatCard
          label="Total users"
          value={data.total_users}
          hint={`${data.active_users} active`}
        />
        <StatCard
          label="Subscriptions"
          value={data.active_subscriptions}
          hint={`${data.total_subscriptions} total`}
        />
        <StatCard label="Open tickets" value={data.open_tickets} />
        <StatCard
          label="Broker connections"
          value={data.broker_connections}
          hint={`${data.broker_errors} errors`}
        />
        <StatCard label="Feature flags" value={data.enabled_feature_flags} hint="enabled" />
        <StatCard label="Announcements" value={data.published_announcements} hint="published" />
      </FadeInStagger>
    </div>
  );
}
