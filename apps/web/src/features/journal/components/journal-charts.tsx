'use client';

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import type {
  CalendarDay,
  EmotionStats,
  MistakeStats,
  StrategyPerformance,
  SymbolPerformance,
  WeekdayPerformance,
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

import { formatCurrency } from '@/features/journal/utils/format';

const chartTooltipStyle = {
  backgroundColor: 'hsl(240 5% 7%)',
  border: '1px solid hsl(240 4% 14%)',
  borderRadius: '8px',
  fontSize: '12px',
};

function calendarColor(pnl: number): string {
  if (pnl > 800) return 'bg-profit';
  if (pnl > 200) return 'bg-profit/70';
  if (pnl > 0) return 'bg-profit/40';
  if (pnl > -200) return 'bg-loss/40';
  if (pnl > -800) return 'bg-loss/70';
  return 'bg-loss';
}

export function JournalCalendar({ data }: { data: CalendarDay[] }) {
  const weeks: CalendarDay[][] = [];
  for (let i = 0; i < data.length; i += 7) {
    weeks.push(data.slice(i, i + 7));
  }

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Calendar View</CardTitle>
        <CardDescription>Daily P&L heatmap</CardDescription>
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
      </CardContent>
    </Card>
  );
}

export function StrategyPerformanceChart({ data }: { data: StrategyPerformance[] }) {
  const chartData = data.map((s) => ({
    name: s.strategy_name.length > 14 ? `${s.strategy_name.slice(0, 12)}…` : s.strategy_name,
    pnl: s.total_pnl,
    fill: s.color ?? '#64748b',
    winRate: s.win_rate,
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Performance by Strategy</CardTitle>
        <CardDescription>Total P&L and win rate per strategy</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 10 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) => `$${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
              width={44}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value, _name, props) => {
                const payload = props.payload as { winRate: number };
                return [
                  `${formatCurrency(Number(value))} · ${payload.winRate.toFixed(0)}% WR`,
                  'P&L',
                ];
              }}
            />
            <Bar dataKey="pnl" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function EmotionPerformanceChart({ data }: { data: EmotionStats[] }) {
  const chartData = data.slice(0, 6).map((e) => ({
    emotion: e.emotion,
    pnl: e.total_pnl,
    fill: e.total_pnl >= 0 ? 'hsl(142 71% 45%)' : 'hsl(0 84% 60%)',
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Performance by Emotion</CardTitle>
        <CardDescription>How emotions correlate with outcomes</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
          >
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) => `$${v}`}
            />
            <YAxis
              type="category"
              dataKey="emotion"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              width={72}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value) => [formatCurrency(Number(value)), 'P&L']}
            />
            <Bar dataKey="pnl" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function WeekdayPerformanceChart({ data }: { data: WeekdayPerformance[] }) {
  const chartData = data.map((d) => ({
    name: d.weekday.slice(0, 3),
    pnl: d.total_pnl,
    winRate: d.win_rate,
    fill: d.total_pnl >= 0 ? 'hsl(142 71% 45%)' : 'hsl(0 84% 60%)',
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Performance by Weekday</CardTitle>
        <CardDescription>P&L distribution across trading days</CardDescription>
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
              width={44}
              tickFormatter={(v: number) => `$${v}`}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value, _n, props) => {
                const payload = props.payload as { winRate: number };
                return [
                  `${formatCurrency(Number(value))} · ${payload.winRate.toFixed(0)}% WR`,
                  'P&L',
                ];
              }}
            />
            <Bar dataKey="pnl" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function SymbolPerformanceChart({ data }: { data: SymbolPerformance[] }) {
  const chartData = data.slice(0, 8).map((s) => ({
    symbol: s.symbol,
    pnl: s.total_pnl,
    fill: s.total_pnl >= 0 ? 'hsl(142 71% 45%)' : 'hsl(0 84% 60%)',
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Performance by Symbol</CardTitle>
        <CardDescription>Top symbols by total P&L</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
          >
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) => `$${v}`}
            />
            <YAxis
              type="category"
              dataKey="symbol"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              width={48}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value) => [formatCurrency(Number(value)), 'P&L']}
            />
            <Bar dataKey="pnl" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function MistakeStatsChart({ data }: { data: MistakeStats[] }) {
  const chartData = data.slice(0, 8).map((m) => ({
    mistake: m.mistake.length > 18 ? `${m.mistake.slice(0, 16)}…` : m.mistake,
    count: m.count,
    fill: 'hsl(0 84% 60%)',
  }));

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Most Common Mistakes</CardTitle>
        <CardDescription>Frequency of logged mistakes</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
          >
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              allowDecimals={false}
            />
            <YAxis
              type="category"
              dataKey="mistake"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 10 }}
              width={100}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value) => [String(value), 'Count']}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
