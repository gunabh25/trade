import type { AnalyticsOverview } from '@tradeflow/types/api';
import type { BrokerConnection, BrokerOrder, BrokerPosition } from '@tradeflow/types/api';

import { getAnalyticsOverview } from '@/features/analytics/api/analytics-api';
import {
  listBrokerAccounts,
  listBrokerConnections,
  listBrokerOrders,
  listBrokerPositions,
} from '@/features/broker/api/broker-api';
import { listRiskBreaches, listRiskRules } from '@/features/risk/api/risk-api';
import { formatRelativeTime, toNumber } from '@/lib/api/normalize';

import type {
  CalendarDay,
  ConnectedAccount,
  DashboardData,
  EquityPoint,
  Notification,
  Order,
  Position,
  ReturnPoint,
  Workspace,
} from '@/features/dashboard/data/mock-dashboard-data';

function mapConnectionStatus(connection: BrokerConnection): ConnectedAccount['status'] {
  if (connection.status === 'connected') return 'connected';
  if (connection.status === 'error') return 'error';
  return 'disconnected';
}

function mapPositionSide(side: string): Position['side'] {
  return side.toLowerCase().includes('short') ? 'short' : 'long';
}

function mapOrderSide(side: string): Order['side'] {
  return side.toLowerCase() === 'sell' ? 'sell' : 'buy';
}

function mapOrderStatus(status: string): Order['status'] {
  const normalized = status.toLowerCase();
  if (normalized.includes('partial')) return 'partial';
  if (normalized.includes('pending')) return 'pending';
  return 'open';
}

function mapPosition(position: BrokerPosition): Position {
  const entry = position.entry_price;
  const pnl = position.unrealized_pnl;
  const pnlPercent = entry !== 0 ? (pnl / (entry * position.quantity)) * 100 : 0;

  return {
    id: position.id,
    symbol: position.symbol,
    side: mapPositionSide(position.side),
    quantity: position.quantity,
    entryPrice: entry,
    markPrice: position.mark_price,
    pnl,
    pnlPercent,
  };
}

function mapOrder(order: BrokerOrder): Order {
  return {
    id: order.id,
    symbol: order.symbol,
    side: mapOrderSide(order.side),
    type: order.order_type,
    quantity: order.quantity,
    price: order.price ?? 0,
    status: mapOrderStatus(order.status),
  };
}

function formatChartDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString('en-US', { month: 'short' });
}

function buildWorkspaces(connections: BrokerConnection[]): Workspace[] {
  if (connections.length === 0) {
    return [{ id: 'default', name: 'My Portfolio', plan: 'Pro' }];
  }
  return connections.map((connection) => ({
    id: connection.id,
    name: connection.name,
    plan: connection.broker === 'paper' ? 'Free' : 'Pro',
  }));
}

function buildNotificationsFromBreaches(
  breaches: Awaited<ReturnType<typeof listRiskBreaches>>,
): Notification[] {
  return breaches.slice(0, 8).map((breach) => ({
    id: breach.id,
    title: 'Risk breach detected',
    message: breach.message,
    time: formatRelativeTime(breach.created_at),
    read: false,
    type: 'risk' as const,
  }));
}

function deriveRiskStatus(
  rules: Awaited<ReturnType<typeof listRiskRules>>,
  analytics: AnalyticsOverview | null,
): { riskStatus: DashboardData['stats']['riskStatus']; riskScore: number } {
  if (rules.some((rule) => rule.kill_switch_active)) {
    return { riskStatus: 'high', riskScore: 92 };
  }

  const maxDrawdown = Math.abs(analytics?.metrics.max_drawdown_pct ?? 0);
  if (maxDrawdown >= 10) {
    return { riskStatus: 'high', riskScore: 78 };
  }
  if (maxDrawdown >= 5) {
    return { riskStatus: 'medium', riskScore: 52 };
  }
  return { riskStatus: 'low', riskScore: 24 };
}

function buildStats(
  accounts: ConnectedAccount[],
  positions: Position[],
  orders: Order[],
  analytics: AnalyticsOverview | null,
  risk: { riskStatus: DashboardData['stats']['riskStatus']; riskScore: number },
): DashboardData['stats'] {
  const accountEquity = accounts.reduce((sum, account) => sum + account.equity, 0);
  const totalEquity = accountEquity > 0 ? accountEquity : (analytics?.metrics.ending_equity ?? 0);

  const todayPnl = analytics?.daily_returns.at(-1)?.value ?? 0;
  const todayPnlPercent = totalEquity > 0 ? (todayPnl / totalEquity) * 100 : 0;
  const monthlyPnl = analytics?.monthly_returns.at(-1)?.value ?? 0;
  const monthlyPnlPercent = totalEquity > 0 ? (monthlyPnl / totalEquity) * 100 : 0;

  return {
    totalEquity,
    todayPnl,
    todayPnlPercent,
    monthlyPnl,
    monthlyPnlPercent,
    openPositions: positions.length,
    openOrders: orders.length,
    connectedAccounts: accounts.filter((account) => account.status === 'connected').length,
    riskStatus: risk.riskStatus,
    riskScore: risk.riskScore,
  };
}

function buildEquityCurve(analytics: AnalyticsOverview | null): EquityPoint[] {
  if (!analytics?.equity_curve.length) {
    return [];
  }
  const step = Math.max(1, Math.floor(analytics.equity_curve.length / 12));
  return analytics.equity_curve
    .filter((_, index) => index % step === 0 || index === analytics.equity_curve.length - 1)
    .map((point) => ({
      date: formatChartDate(point.date),
      equity: point.equity,
    }));
}

function buildProfitCalendar(analytics: AnalyticsOverview | null): CalendarDay[] {
  return (analytics?.calendar_heatmap ?? []).map((day) => ({
    date: day.date,
    pnl: day.pnl,
  }));
}

function buildDailyReturns(analytics: AnalyticsOverview | null): ReturnPoint[] {
  return (analytics?.daily_returns ?? []).map((point) => ({
    label: point.label,
    value: point.value,
  }));
}

function buildMonthlyReturns(analytics: AnalyticsOverview | null): ReturnPoint[] {
  return (analytics?.monthly_returns ?? []).map((point) => ({
    label: point.label,
    value: point.value,
  }));
}

export async function fetchDashboardData(): Promise<DashboardData> {
  const [connections, analytics, breaches, rules] = await Promise.all([
    listBrokerConnections().catch(() => [] as BrokerConnection[]),
    getAnalyticsOverview().catch(() => null),
    listRiskBreaches().catch(() => []),
    listRiskRules().catch(() => []),
  ]);

  const accounts: ConnectedAccount[] = [];
  const positions: Position[] = [];
  const orders: Order[] = [];

  await Promise.all(
    connections.map(async (connection) => {
      if (connection.status !== 'connected') {
        accounts.push({
          id: connection.id,
          name: connection.name,
          broker: connection.broker,
          status: mapConnectionStatus(connection),
          equity: 0,
          lastSync: formatRelativeTime(connection.last_connected_at),
        });
        return;
      }

      try {
        const brokerAccounts = await listBrokerAccounts(connection.id);
        for (const account of brokerAccounts) {
          accounts.push({
            id: account.id,
            name: account.name,
            broker: connection.broker,
            status: mapConnectionStatus(connection),
            equity: account.equity,
            lastSync: formatRelativeTime(connection.last_connected_at),
          });

          const [accountPositions, accountOrders] = await Promise.all([
            listBrokerPositions(connection.id, account.id).catch(() => []),
            listBrokerOrders(connection.id, account.id).catch(() => []),
          ]);

          positions.push(...accountPositions.map(mapPosition));
          orders.push(...accountOrders.map(mapOrder));
        }
      } catch {
        accounts.push({
          id: connection.id,
          name: connection.name,
          broker: connection.broker,
          status: mapConnectionStatus(connection),
          equity: 0,
          lastSync: formatRelativeTime(connection.last_connected_at),
        });
      }
    }),
  );

  const workspaces = buildWorkspaces(connections);
  const risk = deriveRiskStatus(rules, analytics);
  const notifications = buildNotificationsFromBreaches(breaches);

  return {
    workspaces,
    activeWorkspaceId: workspaces[0]?.id ?? 'default',
    stats: buildStats(accounts, positions, orders, analytics, risk),
    equityCurve: buildEquityCurve(analytics),
    profitCalendar: buildProfitCalendar(analytics),
    dailyReturns: buildDailyReturns(analytics),
    monthlyReturns: buildMonthlyReturns(analytics),
    positions,
    orders,
    accounts,
    notifications,
  };
}

export function isDashboardEmpty(data: DashboardData): boolean {
  const hasBrokerData = data.accounts.length > 0;
  const hasAnalytics =
    data.equityCurve.length > 0 ||
    data.profitCalendar.length > 0 ||
    toNumber(data.stats.totalEquity) > 0;
  return !hasBrokerData && !hasAnalytics;
}
