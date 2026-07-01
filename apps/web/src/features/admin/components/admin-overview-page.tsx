'use client';

import { AlertCircle } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from '@tradeflow/ui';

import { formatMrr, getAdminAnalytics, getAdminOverview } from '@/features/admin/api/admin-api';
import {
  AdminBarChart,
  AdminLineChart,
  AdminPieChart,
} from '@/features/admin/components/admin-charts';
import { AdminObservabilityDashboard } from '@/features/admin/components/admin-enterprise-pages';
import { AdminPageHeader, StatCard } from '@/features/admin/components/admin-ui';
import { EmptyState, FadeInStagger } from '@/features/dashboard/components/motion-primitives';

export function AdminOverviewPage() {
  const [overview, setOverview] = useState<Awaited<ReturnType<typeof getAdminOverview>> | null>(
    null,
  );
  const [analytics, setAnalytics] = useState<Awaited<ReturnType<typeof getAdminAnalytics>> | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [overviewResult, analyticsResult] = await Promise.allSettled([
      getAdminOverview(),
      getAdminAnalytics(),
    ]);

    if (overviewResult.status === 'fulfilled') {
      setOverview(overviewResult.value);
      setError(null);
    } else {
      setOverview(null);
      setError(
        overviewResult.reason instanceof Error
          ? overviewResult.reason.message
          : 'Failed to load overview',
      );
    }

    if (analyticsResult.status === 'fulfilled') {
      setAnalytics(analyticsResult.value);
    } else {
      setAnalytics(null);
    }

    setLoading(false);
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

  if (error || !overview) {
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

  const userGrowth =
    analytics?.users_by_month.map((row) => ({
      month: String(row.month),
      count: Number(row.count),
    })) ?? [];

  const subsByPlan =
    analytics?.subscriptions_by_plan.map((p) => ({
      name: p.name,
      value: p.count,
    })) ?? [];

  return (
    <div>
      <AdminPageHeader
        title="Dashboard"
        description="Platform metrics, growth charts, and live system status."
      />
      <FadeInStagger className="grid gap-4 p-4 sm:grid-cols-2 sm:p-6 xl:grid-cols-4">
        <StatCard
          label="Total users"
          value={overview.total_users}
          hint={`${overview.active_users} active`}
        />
        <StatCard
          label="Subscriptions"
          value={overview.active_subscriptions}
          hint={`${overview.total_subscriptions} total`}
        />
        <StatCard label="Organizations" value={overview.total_organizations ?? 0} />
        <StatCard label="Trading accounts" value={overview.total_trading_accounts ?? 0} />
        <StatCard label="Open tickets" value={overview.open_tickets} />
        <StatCard
          label="Broker connections"
          value={overview.broker_connections}
          hint={`${overview.broker_errors} errors`}
        />
        <StatCard label="MRR" value={formatMrr(analytics?.mrr_cents ?? 0)} />
        <StatCard label="Feature flags" value={overview.enabled_feature_flags} hint="enabled" />
      </FadeInStagger>

      <div className="grid gap-4 p-4 sm:p-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">User growth</CardTitle>
          </CardHeader>
          <CardContent>
            <AdminLineChart data={userGrowth} xKey="month" yKey="count" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Subscriptions by plan</CardTitle>
          </CardHeader>
          <CardContent>
            <AdminPieChart data={subsByPlan} nameKey="name" valueKey="value" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Tickets by status</CardTitle>
          </CardHeader>
          <CardContent>
            <AdminBarChart
              data={
                analytics?.tickets_by_status.map((t) => ({
                  status: t.status,
                  count: t.count,
                })) ?? []
              }
              xKey="status"
              yKey="count"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Connections by broker</CardTitle>
          </CardHeader>
          <CardContent>
            <AdminBarChart
              data={
                analytics?.connections_by_broker.map((c) => ({
                  broker: c.broker,
                  count: c.count,
                })) ?? []
              }
              xKey="broker"
              yKey="count"
            />
          </CardContent>
        </Card>
      </div>

      <div className="p-4 sm:p-6">
        <AdminObservabilityDashboard />
      </div>
    </div>
  );
}
