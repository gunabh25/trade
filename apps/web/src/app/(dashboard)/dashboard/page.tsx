'use client';

import { LayoutDashboard } from 'lucide-react';

import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@tradeflow/ui';

import {
  DailyReturnsChart,
  EquityCurveChart,
  MonthlyReturnsChart,
  ProfitCalendar,
} from '@/features/dashboard/components/charts';
import { DashboardSkeleton } from '@/features/dashboard/components/dashboard-skeleton';
import {
  ConnectedAccountsList,
  OpenOrdersTable,
  OpenPositionsTable,
  RiskStatusPanel,
} from '@/features/dashboard/components/data-panels';
import {
  EmptyState,
  FadeInItem,
  FadeInStagger,
} from '@/features/dashboard/components/motion-primitives';
import { StatWidgetsGrid } from '@/features/dashboard/components/stat-widgets';
import { useDashboardData } from '@/features/dashboard/hooks/use-dashboard-data';

export default function DashboardPage() {
  const { data, loading, isEmpty } = useDashboardData();

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (isEmpty || !data) {
    return (
      <div className="p-4 sm:p-6">
        <EmptyState
          icon={LayoutDashboard}
          title="No trading data yet"
          description="Connect your first broker account to see equity, positions, and performance analytics."
          action={<Button size="sm">Connect account</Button>}
        />
      </div>
    );
  }

  return (
    <FadeInStagger className="space-y-6 p-4 sm:p-6">
      <FadeInItem>
        <StatWidgetsGrid stats={data.stats} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <EquityCurveChart data={data.equityCurve} />
        </div>
        <div className="lg:col-span-2">
          <ProfitCalendar data={data.profitCalendar} />
        </div>
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-2">
        <DailyReturnsChart data={data.dailyReturns} />
        <MonthlyReturnsChart data={data.monthlyReturns} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 lg:grid-cols-3">
        <Card className="border-border/60 bg-card/80 shadow-none lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-medium">Open Positions</CardTitle>
            <CardDescription>Live positions across all accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <OpenPositionsTable positions={data.positions} />
          </CardContent>
        </Card>
        <RiskStatusPanel riskStatus={data.stats.riskStatus} riskScore={data.stats.riskScore} />
      </FadeInItem>

      <FadeInItem className="grid gap-4 md:grid-cols-2">
        <Card className="border-border/60 bg-card/80 shadow-none">
          <CardHeader>
            <CardTitle className="text-base font-medium">Open Orders</CardTitle>
            <CardDescription>Pending and partial fills</CardDescription>
          </CardHeader>
          <CardContent>
            <OpenOrdersTable orders={data.orders} />
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-card/80 shadow-none">
          <CardHeader>
            <CardTitle className="text-base font-medium">Connected Accounts</CardTitle>
            <CardDescription>Broker connections and sync status</CardDescription>
          </CardHeader>
          <CardContent>
            <ConnectedAccountsList accounts={data.accounts} />
          </CardContent>
        </Card>
      </FadeInItem>
    </FadeInStagger>
  );
}
