'use client';

import type { ReactNode } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

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

import type {
  CalendarDay,
  EquityPoint,
  ReturnPoint,
} from '@/features/dashboard/data/mock-dashboard-data';
import { formatCurrency } from '@/features/dashboard/data/mock-dashboard-data';

const chartTooltipStyle = {
  backgroundColor: 'hsl(240 5% 7%)',
  border: '1px solid hsl(240 4% 14%)',
  borderRadius: '8px',
  fontSize: '12px',
};

function ChartFrame({
  height,
  empty,
  emptyMessage,
  children,
}: {
  height: number;
  empty: boolean;
  emptyMessage: string;
  children: ReactNode;
}) {
  if (empty) {
    return (
      <div
        className="text-muted-foreground border-border/60 flex items-center justify-center rounded-md border border-dashed text-center text-sm"
        style={{ height }}
      >
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="w-full min-w-0" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%" debounce={50}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}

export function EquityCurveChart({ data }: { data: EquityPoint[] }) {
  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Equity Curve</CardTitle>
        <CardDescription>Portfolio value over time</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartFrame
          height={280}
          empty={data.length === 0}
          emptyMessage="No equity history yet. Closed trades and account balances will appear here."
        >
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(142 71% 45%)" stopOpacity={0.25} />
                <stop offset="100%" stopColor="hsl(142 71% 45%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="hsl(240 4% 14%)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(240 5% 64%)', fontSize: 11 }}
              tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
              width={48}
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
              fill="url(#equityGradient)"
            />
          </AreaChart>
        </ChartFrame>
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

export function ProfitCalendar({ data }: { data: CalendarDay[] }) {
  const weeks: CalendarDay[][] = [];
  for (let i = 0; i < data.length; i += 7) {
    weeks.push(data.slice(i, i + 7));
  }

  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Profit Calendar</CardTitle>
        <CardDescription>Daily PnL heatmap — last 12 weeks</CardDescription>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="text-muted-foreground border-border/60 flex h-[120px] items-center justify-center rounded-md border border-dashed text-center text-sm">
            No daily PnL yet. Close trades to build your profit calendar.
          </div>
        ) : (
          <>
            <TooltipProvider delayDuration={100}>
              <div className="flex gap-1 overflow-x-auto pb-1">
                {weeks.map((week, weekIndex) => (
                  <div key={weekIndex} className="flex flex-col gap-1">
                    {week.map((day) => (
                      <UiTooltip key={day.date}>
                        <TooltipTrigger asChild>
                          <div
                            className={cn(
                              'h-3.5 w-3.5 rounded-sm transition-opacity hover:opacity-80',
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
          </>
        )}
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
  data: ReturnPoint[];
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
        <ChartFrame height={220} empty={data.length === 0} emptyMessage="No daily returns yet.">
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
              tickFormatter={(v: number) => `$${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
              width={40}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value) => [formatCurrency(Number(value)), 'PnL']}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ChartFrame>
      </CardContent>
    </Card>
  );
}

export function DailyReturnsChart({ data }: { data: ReturnPoint[] }) {
  return (
    <ReturnsBarChart
      title="Daily Returns"
      description="This week's realized PnL by day"
      data={data}
    />
  );
}

export function MonthlyReturnsChart({ data }: { data: ReturnPoint[] }) {
  return (
    <ReturnsBarChart
      title="Monthly Returns"
      description="Year-to-date monthly performance"
      data={data}
    />
  );
}
