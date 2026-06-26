'use client';

import dynamic from 'next/dynamic';
import { LineChart } from 'lucide-react';

import { Button, Skeleton } from '@tradeflow/ui';

import { AnalyticsFilters } from '@/features/analytics/components/analytics-filters';
import { AnalyticsMetricsGrid } from '@/features/analytics/components/analytics-stats-bar';
import { useAnalyticsData } from '@/features/analytics/hooks/use-analytics-data';
import {
  EmptyState,
  FadeInItem,
  FadeInStagger,
} from '@/features/dashboard/components/motion-primitives';

const AnalyticsChartSections = dynamic(
  () =>
    import('@/features/analytics/components/analytics-chart-sections').then((mod) => ({
      default: mod.AnalyticsChartSections,
    })),
  {
    loading: () => <ChartSectionsSkeleton />,
    ssr: false,
  },
);

function AnalyticsSkeleton() {
  return (
    <div className="space-y-6 p-4 sm:p-6">
      <Skeleton className="h-8 w-48" />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-[360px]" />
        <Skeleton className="h-[360px]" />
      </div>
    </div>
  );
}

function ChartSectionsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 xl:grid-cols-2">
        <Skeleton className="h-[340px]" />
        <Skeleton className="h-[340px]" />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-[280px]" />
        <Skeleton className="h-[280px]" />
      </div>
    </div>
  );
}

export function AnalyticsPage() {
  const analyticsData = useAnalyticsData();
  const { data, loading, error, refetch } = analyticsData;

  if (loading) {
    return <AnalyticsSkeleton />;
  }

  if (error || !data) {
    return (
      <div className="p-4 sm:p-6">
        <EmptyState
          icon={LineChart}
          title="Could not load analytics"
          description={error ?? 'No analytics data available yet.'}
          action={
            <Button size="sm" onClick={() => void refetch()}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <FadeInStagger className="space-y-6 p-4 sm:p-6">
      <FadeInItem>
        <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <LineChart className="text-primary h-5 w-5" />
              <h1 className="text-xl font-semibold tracking-tight">Enterprise Analytics</h1>
            </div>
            <p className="text-muted-foreground mt-1 text-sm">
              Institutional-grade performance metrics, risk ratios, and comparative analysis
            </p>
          </div>
          <p className="text-muted-foreground text-xs tabular-nums">
            {data.metrics.total_trades.toLocaleString()} trades ·{' '}
            {data.metrics.starting_equity.toLocaleString('en-US', {
              style: 'currency',
              currency: 'USD',
              maximumFractionDigits: 0,
            })}{' '}
            →{' '}
            {data.metrics.ending_equity.toLocaleString('en-US', {
              style: 'currency',
              currency: 'USD',
              maximumFractionDigits: 0,
            })}
          </p>
        </div>
      </FadeInItem>

      <FadeInItem>
        <AnalyticsFilters data={analyticsData} />
      </FadeInItem>

      <FadeInItem>
        <AnalyticsMetricsGrid metrics={data.metrics} />
      </FadeInItem>

      <AnalyticsChartSections data={data} />
    </FadeInStagger>
  );
}
