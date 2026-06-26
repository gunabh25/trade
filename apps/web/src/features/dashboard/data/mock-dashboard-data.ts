export interface Workspace {
  id: string;
  name: string;
  plan: string;
}

export interface DashboardStats {
  totalEquity: number;
  todayPnl: number;
  todayPnlPercent: number;
  monthlyPnl: number;
  monthlyPnlPercent: number;
  openPositions: number;
  openOrders: number;
  connectedAccounts: number;
  riskStatus: 'low' | 'medium' | 'high';
  riskScore: number;
}

export interface EquityPoint {
  date: string;
  equity: number;
}

export interface ReturnPoint {
  label: string;
  value: number;
}

export interface CalendarDay {
  date: string;
  pnl: number;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  markPrice: number;
  pnl: number;
  pnlPercent: number;
}

export interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: string;
  quantity: number;
  price: number;
  status: 'open' | 'partial' | 'pending';
}

export interface ConnectedAccount {
  id: string;
  name: string;
  broker: string;
  status: 'connected' | 'disconnected' | 'error';
  equity: number;
  lastSync: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
  type: 'trade' | 'risk' | 'system';
}

export interface DashboardData {
  workspaces: Workspace[];
  activeWorkspaceId: string;
  stats: DashboardStats;
  equityCurve: EquityPoint[];
  profitCalendar: CalendarDay[];
  dailyReturns: ReturnPoint[];
  monthlyReturns: ReturnPoint[];
  positions: Position[];
  orders: Order[];
  accounts: ConnectedAccount[];
  notifications: Notification[];
}

export const mockDashboardData: DashboardData = {
  workspaces: [
    { id: 'ws-1', name: 'Primary Portfolio', plan: 'Pro' },
    { id: 'ws-2', name: 'Prop Firm Alpha', plan: 'Enterprise' },
    { id: 'ws-3', name: 'Paper Trading', plan: 'Free' },
  ],
  activeWorkspaceId: 'ws-1',
  stats: {
    totalEquity: 284_750.42,
    todayPnl: 3_842.18,
    todayPnlPercent: 1.37,
    monthlyPnl: 18_920.55,
    monthlyPnlPercent: 7.12,
    openPositions: 12,
    openOrders: 4,
    connectedAccounts: 5,
    riskStatus: 'low',
    riskScore: 24,
  },
  equityCurve: [
    { date: 'Jan', equity: 245_000 },
    { date: 'Feb', equity: 251_200 },
    { date: 'Mar', equity: 248_900 },
    { date: 'Apr', equity: 256_400 },
    { date: 'May', equity: 262_100 },
    { date: 'Jun', equity: 259_800 },
    { date: 'Jul', equity: 268_300 },
    { date: 'Aug', equity: 271_500 },
    { date: 'Sep', equity: 269_200 },
    { date: 'Oct', equity: 275_600 },
    { date: 'Nov', equity: 280_100 },
    { date: 'Dec', equity: 284_750 },
  ],
  profitCalendar: Array.from({ length: 84 }, (_, index) => {
    const day = index + 1;
    const pnl = Math.sin(day / 4) * 1200 + (Math.random() - 0.45) * 800;
    return {
      date: `2026-${String(Math.floor(day / 28) + 1).padStart(2, '0')}-${String((day % 28) + 1).padStart(2, '0')}`,
      pnl: Math.round(pnl * 100) / 100,
    };
  }),
  dailyReturns: [
    { label: 'Mon', value: 420 },
    { label: 'Tue', value: -180 },
    { label: 'Wed', value: 890 },
    { label: 'Thu', value: 310 },
    { label: 'Fri', value: 1240 },
    { label: 'Sat', value: 0 },
    { label: 'Sun', value: 142 },
  ],
  monthlyReturns: [
    { label: 'Jan', value: 4200 },
    { label: 'Feb', value: 6800 },
    { label: 'Mar', value: -2100 },
    { label: 'Apr', value: 5400 },
    { label: 'May', value: 8900 },
    { label: 'Jun', value: 3200 },
    { label: 'Jul', value: 7600 },
    { label: 'Aug', value: 4100 },
    { label: 'Sep', value: -900 },
    { label: 'Oct', value: 6200 },
    { label: 'Nov', value: 9800 },
    { label: 'Dec', value: 18920 },
  ],
  positions: [
    {
      id: '1',
      symbol: 'ES',
      side: 'long',
      quantity: 4,
      entryPrice: 5842.25,
      markPrice: 5856.5,
      pnl: 1140,
      pnlPercent: 0.24,
    },
    {
      id: '2',
      symbol: 'NQ',
      side: 'long',
      quantity: 2,
      entryPrice: 21240,
      markPrice: 21305,
      pnl: 1300,
      pnlPercent: 0.31,
    },
    {
      id: '3',
      symbol: 'CL',
      side: 'short',
      quantity: 3,
      entryPrice: 72.45,
      markPrice: 71.9,
      pnl: 495,
      pnlPercent: 0.76,
    },
    {
      id: '4',
      symbol: 'GC',
      side: 'long',
      quantity: 1,
      entryPrice: 2648,
      markPrice: 2642,
      pnl: -600,
      pnlPercent: -0.23,
    },
  ],
  orders: [
    { id: '1', symbol: 'ES', side: 'buy', type: 'Limit', quantity: 2, price: 5835, status: 'open' },
    {
      id: '2',
      symbol: 'NQ',
      side: 'sell',
      type: 'Stop',
      quantity: 1,
      price: 21180,
      status: 'open',
    },
    {
      id: '3',
      symbol: 'YM',
      side: 'buy',
      type: 'Limit',
      quantity: 3,
      price: 44120,
      status: 'partial',
    },
  ],
  accounts: [
    {
      id: '1',
      name: 'Apex 150K',
      broker: 'Tradovate',
      status: 'connected',
      equity: 152_340,
      lastSync: '2m ago',
    },
    {
      id: '2',
      name: 'Topstep 100K',
      broker: 'Rithmic',
      status: 'connected',
      equity: 98_720,
      lastSync: '5m ago',
    },
    {
      id: '3',
      name: 'Personal IBKR',
      broker: 'Interactive Brokers',
      status: 'connected',
      equity: 33_690,
      lastSync: '1m ago',
    },
    {
      id: '4',
      name: 'Paper Sim',
      broker: 'Tradovate',
      status: 'disconnected',
      equity: 0,
      lastSync: '3h ago',
    },
  ],
  notifications: [
    {
      id: '1',
      title: 'Copy trade executed',
      message: 'ES long x2 copied to Apex 150K',
      time: '2m ago',
      read: false,
      type: 'trade',
    },
    {
      id: '2',
      title: 'Risk limit warning',
      message: 'Daily drawdown at 72% of limit',
      time: '18m ago',
      read: false,
      type: 'risk',
    },
    {
      id: '3',
      title: 'Account synced',
      message: 'Topstep 100K balance updated',
      time: '1h ago',
      read: true,
      type: 'system',
    },
    {
      id: '4',
      title: 'Order filled',
      message: 'NQ limit buy filled at 21240',
      time: '2h ago',
      read: true,
      type: 'trade',
    },
  ],
};

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export function formatPnl(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${formatCurrency(value)}`;
}
