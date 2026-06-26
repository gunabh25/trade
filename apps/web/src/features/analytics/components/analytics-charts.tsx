'use client';

import { Fragment } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type {
  AnalyticsCalendarDay,
  AnalyticsComparisonSeries,
  AnalyticsDrawdownPoint,
  AnalyticsEquityPoint,
  AnalyticsHourCell,
  AnalyticsPieSlice,
  AnalyticsReturnPoint,
} from '@tradeflow/types/api';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Tooltip as UiTooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
  cn,
} from '@tradeflow/ui';

import {
  DAY_LABELS,
  formatCompactDate,
  formatCurrency,
  formatPercent,
} from '@/features/analytics/data/mock-analytics-data';

const chartTooltipStyle = {
  backgroundColor: 'hsl(240 5% 7%)',
  border: '1px solid hsl(240 4% 14%)',
  borderRadius: '8px',
  fontSize: '12px',
};

export function EquityCurveChart({ data }: { data: AnalyticsEquityPoint[] }) {
  const sampled = data.filter((_, i) => i % Math.max(1, Math.floor(data.length / 60)) === 0);
  const chartData = sampled.map((p) => ({
    ...p,
    label: formatCompactDate(p.date),
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Equity Curve</CardTitle>
        <CardDescription>Cumulative portfolio value</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="analyticsEquityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(142 71% 45%)" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(142 71% 45%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
              width={52}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value) => [formatCurrency(Number(value)), 'Equity']}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="hsl(142 71% 45%)"
              strokeWidth={2}
              fill="url(#analyticsEquityGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function DrawdownChart({ data }: { data: AnalyticsDrawdownPoint[] }) {
  const sampled = data.filter((_, i) => i % Math.max(1, Math.floor(data.length / 60)) === 0);
  const chartData = sampled.map((p) => ({
    ...p,
    label: formatCompactDate(p.date),
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Drawdown</CardTitle>
        <CardDescription>Underwater equity from peak (%)</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(0 84% 60%)" stopOpacity={0.15} />
                <stop offset="100%" stopColor="hsl(0 84% 60%)" stopOpacity={0.4} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              width={44}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value) => [formatPercent(Number(value)), 'Drawdown']}
            />
            <Area
              type="monotone"
              dataKey="drawdown_pct"
              stroke="hsl(0 84% 60%)"
              strokeWidth={1.5}
              fill="url(#drawdownGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function ReturnsBarChart({
  title,
  description,
  data,
}: {
  title: string;
  description: string;
  data: AnalyticsReturnPoint[];
}) {
  const chartData = data.map((entry) => ({
    ...entry,
    fill: entry.value >= 0 ? 'hsl(142 71% 45%)' : 'hsl(0 84% 60%)',
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) =>
                `$${Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`
              }
              width={44}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value) => [formatCurrency(Number(value)), 'PnL']}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function DailyReturnsChart({ data }: { data: AnalyticsReturnPoint[] }) {
  return (
    <ReturnsBarChart title="Daily Returns" description="Realized P&L by trading day" data={data} />
  );
}

export function MonthlyReturnsChart({ data }: { data: AnalyticsReturnPoint[] }) {
  return (
    <ReturnsBarChart
      title="Monthly Returns"
      description="Aggregated monthly performance"
      data={data}
    />
  );
}

export function WinRateChart({
  winRate,
  winCount,
  lossCount,
}: {
  winRate: number;
  winCount: number;
  lossCount: number;
}) {
  const chartData = [
    { name: 'Wins', value: winCount, fill: '#22c55e' },
    { name: 'Losses', value: lossCount, fill: '#ef4444' },
  ];

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Win Rate</CardTitle>
        <CardDescription>Win vs loss distribution</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-center sm:text-left">
            <p className="text-4xl font-semibold tabular-nums tracking-tight">
              {winRate.toFixed(1)}%
            </p>
            <p className="text-muted-foreground mt-1 text-sm">
              {winCount} wins · {lossCount} losses
            </p>
          </div>
          <ResponsiveContainer width="100%" height={180} className="max-w-[200px]">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={52}
                outerRadius={72}
                paddingAngle={3}
                strokeWidth={0}
              />
              <Tooltip contentStyle={chartTooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

export function ProfitFactorChart({
  profitFactor,
  winRate,
}: {
  profitFactor: number | null;
  winRate: number;
}) {
  const pf = profitFactor ?? 0;
  const chartData = [
    { metric: 'Profit Factor', value: Math.min(pf, 4), fill: '#22c55e' },
    { metric: 'Win Rate', value: winRate / 25, fill: '#3b82f6' },
    { metric: 'Benchmark', value: 1, fill: '#64748b' },
  ];

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Profit Factor</CardTitle>
        <CardDescription>Gross profit relative to gross loss</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="mb-4 text-3xl font-semibold tabular-nums">
          {profitFactor?.toFixed(2) ?? '—'}
        </p>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
          >
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" hide domain={[0, 4]} />
            <YAxis
              type="category"
              dataKey="metric"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              width={88}
            />
            <Tooltip contentStyle={chartTooltipStyle} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function calendarColor(pnl: number): string {
  if (pnl > 800) return 'bg-profit';
  if (pnl > 200) return 'bg-profit/70';
  if (pnl > 0) return 'bg-profit/40';
  if (pnl > -200) return 'bg-loss/40';
  if (pnl > -800) return 'bg-loss/70';
  return 'bg-loss';
}

export function CalendarHeatmap({ data }: { data: AnalyticsCalendarDay[] }) {
  const weeks: AnalyticsCalendarDay[][] = [];
  for (let i = 0; i < data.length; i += 7) {
    weeks.push(data.slice(i, i + 7));
  }

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">P&L Heatmap</CardTitle>
        <CardDescription>Daily performance calendar</CardDescription>
      </CardHeader>
      <CardContent>
        <TooltipProvider delayDuration={100}>
          <div className="flex gap-1 overflow-x-auto pb-1">
            {weeks.map((week, weekIndex) => (
              <div key={weekIndex} className="flex flex-col gap-1">
                {week.map((day) => (
                  <UiTooltip key={day.date}>
                    <TooltipTrigger asChild>
                      <div
                        className={cn(
                          'h-4 w-4 rounded-sm transition-opacity hover:opacity-80 sm:h-5 sm:w-5',
                          calendarColor(day.pnl),
                        )}
                      />
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      <p className="font-medium">{day.date}</p>
                      <p className={day.pnl >= 0 ? 'text-profit' : 'text-loss'}>
                        {day.pnl >= 0 ? '+' : ''}
                        {formatCurrency(day.pnl)}
                      </p>
                      <p className="text-muted-foreground">{day.trade_count} trades</p>
                    </TooltipContent>
                  </UiTooltip>
                ))}
              </div>
            ))}
          </div>
        </TooltipProvider>
        <div className="text-muted-foreground mt-4 flex items-center justify-end gap-2 text-[10px]">
          <span>Loss</span>
          <div className="flex gap-0.5">
            <div className="bg-loss h-2.5 w-2.5 rounded-sm" />
            <div className="bg-loss/40 h-2.5 w-2.5 rounded-sm" />
            <div className="bg-muted h-2.5 w-2.5 rounded-sm" />
            <div className="bg-profit/40 h-2.5 w-2.5 rounded-sm" />
            <div className="bg-profit h-2.5 w-2.5 rounded-sm" />
          </div>
          <span>Profit</span>
        </div>
      </CardContent>
    </Card>
  );
}

function hourHeatColor(pnl: number, maxAbs: number): string {
  if (maxAbs === 0) return 'bg-muted';
  const intensity = Math.min(Math.abs(pnl) / maxAbs, 1);
  if (pnl >= 0) {
    if (intensity > 0.7) return 'bg-profit';
    if (intensity > 0.35) return 'bg-profit/70';
    return 'bg-profit/40';
  }
  if (intensity > 0.7) return 'bg-loss';
  if (intensity > 0.35) return 'bg-loss/70';
  return 'bg-loss/40';
}

export function HourDayHeatmap({ data }: { data: AnalyticsHourCell[] }) {
  const hours = Array.from(new Set(data.map((c) => c.hour))).sort((a, b) => a - b);
  const maxAbs = Math.max(...data.map((c) => Math.abs(c.pnl)), 1);

  const lookup = new Map<string, AnalyticsHourCell>();
  for (const cell of data) {
    lookup.set(`${cell.day_of_week}-${cell.hour}`, cell);
  }

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Session Heatmap</CardTitle>
        <CardDescription>P&L by day of week and hour (ET)</CardDescription>
      </CardHeader>
      <CardContent>
        <TooltipProvider delayDuration={100}>
          <div className="overflow-x-auto">
            <div
              className="inline-grid gap-1"
              style={{ gridTemplateColumns: `48px repeat(${hours.length}, 1fr)` }}
            >
              <div />
              {hours.map((h) => (
                <div key={h} className="text-muted-foreground text-center text-[10px]">
                  {h}:00
                </div>
              ))}
              {DAY_LABELS.slice(0, 5).map((dayLabel, dow) => (
                <Fragment key={dow}>
                  <div className="text-muted-foreground flex items-center text-[10px]">
                    {dayLabel}
                  </div>
                  {hours.map((hour) => {
                    const cell = lookup.get(`${dow}-${hour}`);
                    const pnl = cell?.pnl ?? 0;
                    return (
                      <UiTooltip key={`${dow}-${hour}`}>
                        <TooltipTrigger asChild>
                          <div
                            className={cn(
                              'h-7 min-w-[28px] rounded-sm transition-opacity hover:opacity-80',
                              cell ? hourHeatColor(pnl, maxAbs) : 'bg-muted/30',
                            )}
                          />
                        </TooltipTrigger>
                        <TooltipContent side="top" className="text-xs">
                          <p className="font-medium">
                            {dayLabel} {hour}:00
                          </p>
                          {cell ? (
                            <>
                              <p className={pnl >= 0 ? 'text-profit' : 'text-loss'}>
                                {pnl >= 0 ? '+' : ''}
                                {formatCurrency(pnl)}
                              </p>
                              <p className="text-muted-foreground">{cell.trade_count} trades</p>
                            </>
                          ) : (
                            <p className="text-muted-foreground">No trades</p>
                          )}
                        </TooltipContent>
                      </UiTooltip>
                    );
                  })}
                </Fragment>
              ))}
            </div>
          </div>
        </TooltipProvider>
      </CardContent>
    </Card>
  );
}

function AnalyticsPieChart({
  title,
  description,
  data,
}: {
  title: string;
  description: string;
  data: AnalyticsPieSlice[];
}) {
  const total = data.reduce((sum, s) => sum + s.value, 0);
  const chartData = data.map((slice, index) => ({
    name: slice.name,
    value: slice.value,
    fill: slice.color ?? `hsl(${index * 45} 70% 50%)`,
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={80}
              paddingAngle={2}
              strokeWidth={0}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value, name) => {
                const pct = total > 0 ? ((Number(value) / total) * 100).toFixed(1) : '0';
                return [`${pct}%`, String(name)];
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value: string) => (
                <span className="text-muted-foreground text-xs">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function WinLossPieChart({ data }: { data: AnalyticsPieSlice[] }) {
  return (
    <AnalyticsPieChart
      title="Win / Loss Mix"
      description="Gross profit vs gross loss magnitude"
      data={data}
    />
  );
}

export function SymbolPieChart({ data }: { data: AnalyticsPieSlice[] }) {
  return (
    <AnalyticsPieChart
      title="Symbol Allocation"
      description="P&L contribution by instrument"
      data={data}
    />
  );
}

export function StrategyPieChart({ data }: { data: AnalyticsPieSlice[] }) {
  return (
    <AnalyticsPieChart
      title="Strategy Mix"
      description="Performance share by strategy"
      data={data}
    />
  );
}

export function PerformanceComparisonChart({ series }: { series: AnalyticsComparisonSeries[] }) {
  const merged = new Map<string, Record<string, number | string>>();
  for (const s of series) {
    for (const point of s.points) {
      const label = formatCompactDate(point.date);
      const row = merged.get(label) ?? { label };
      row[s.id] = point.equity;
      merged.set(label, row);
    }
  }
  const chartData = Array.from(merged.values());

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Performance Comparison</CardTitle>
        <CardDescription>Normalized equity curves across accounts</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
              width={52}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value, _name, props) => {
                const seriesId = String(props.dataKey);
                const match = series.find((s) => s.id === seriesId);
                return [formatCurrency(Number(value)), match?.name ?? seriesId];
              }}
            />
            <Legend
              verticalAlign="top"
              height={36}
              formatter={(value: string) => {
                const match = series.find((s) => s.id === value);
                return (
                  <span className="text-muted-foreground text-xs">{match?.name ?? value}</span>
                );
              }}
            />
            {series.map((s) => (
              <Line
                key={s.id}
                type="monotone"
                dataKey={s.id}
                stroke={s.color}
                strokeWidth={2}
                dot={false}
                name={s.id}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function RatioComparisonChart({
  sharpe,
  sortino,
  averageR,
  profitFactor,
}: {
  sharpe: number | null;
  sortino: number | null;
  averageR: number | null;
  profitFactor: number | null;
}) {
  const chartData = [
    { name: 'Sharpe', value: sharpe ?? 0, fill: '#22c55e' },
    { name: 'Sortino', value: sortino ?? 0, fill: '#3b82f6' },
    { name: 'Avg R', value: averageR ?? 0, fill: '#a855f7' },
    { name: 'PF', value: profitFactor ?? 0, fill: '#f59e0b' },
  ];

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Risk-Adjusted Metrics</CardTitle>
        <CardDescription>Sharpe, Sortino, Average R, and Profit Factor</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              width={32}
            />
            <Tooltip contentStyle={chartTooltipStyle} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function ExpectancyChart({
  expectancy,
  winRate,
  avgWin,
  avgLoss,
}: {
  expectancy: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
}) {
  const chartData = [
    { component: 'Avg Win', value: avgWin, fill: '#22c55e' },
    { component: 'Avg Loss', value: -Math.abs(avgLoss), fill: '#ef4444' },
    { component: 'Expectancy', value: expectancy, fill: '#3b82f6' },
  ];

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Expectancy</CardTitle>
        <CardDescription>
          Expected value per trade at {winRate.toFixed(1)}% win rate
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-3xl font-semibold tabular-nums">{formatCurrency(expectancy)}</p>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="component"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) => `$${v}`}
              width={48}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value) => [formatCurrency(Number(value)), '']}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function AverageRChart({ averageR, winRate }: { averageR: number | null; winRate: number }) {
  const r = averageR ?? 0;
  const chartData = [
    { zone: '< 0R', value: r < 0 ? 1 : 0, fill: '#ef4444' },
    { zone: '0–1R', value: r >= 0 && r < 1 ? 1 : 0, fill: '#f59e0b' },
    { zone: '1–2R', value: r >= 1 && r < 2 ? 1 : 0, fill: '#22c55e' },
    { zone: '2R+', value: r >= 2 ? 1 : 0, fill: '#16a34a' },
  ];

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Average R</CardTitle>
        <CardDescription>Mean R-multiple at {winRate.toFixed(1)}% win rate</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-3xl font-semibold tabular-nums">{averageR?.toFixed(2) ?? '—'}R</p>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="zone"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
            />
            <YAxis hide domain={[0, 1.2]} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
