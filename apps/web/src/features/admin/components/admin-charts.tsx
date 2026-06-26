'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const CHART_COLORS = [
  'hsl(var(--primary))',
  'hsl(var(--chart-2, 142 76% 36%))',
  'hsl(var(--chart-3, 221 83% 53%))',
  'hsl(var(--chart-4, 47 96% 53%))',
  'hsl(var(--chart-5, 0 84% 60%))',
] as const;

function chartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length] ?? CHART_COLORS[0];
}

export function AdminBarChart({
  data,
  xKey,
  yKey,
  height = 280,
}: {
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
  height?: number;
}) {
  if (data.length === 0) {
    return <p className="text-muted-foreground py-12 text-center text-sm">No chart data</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
        <Tooltip
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: 8,
          }}
        />
        <Bar dataKey={yKey} fill={chartColor(0)} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function AdminLineChart({
  data,
  xKey,
  yKey,
  height = 280,
}: {
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
  height?: number;
}) {
  if (data.length === 0) {
    return <p className="text-muted-foreground py-12 text-center text-sm">No chart data</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
        <Tooltip
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: 8,
          }}
        />
        <Line
          type="monotone"
          dataKey={yKey}
          stroke={chartColor(0)}
          strokeWidth={2}
          dot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function AdminPieChart({
  data,
  nameKey,
  valueKey,
  height = 280,
}: {
  data: { name: string; value: number }[];
  nameKey: string;
  valueKey: string;
  height?: number;
}) {
  if (data.length === 0) {
    return <p className="text-muted-foreground py-12 text-center text-sm">No chart data</p>;
  }

  const chartData = data.map((item, index) => ({
    ...item,
    fill: chartColor(index),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey={valueKey}
          nameKey={nameKey}
          cx="50%"
          cy="50%"
          outerRadius={90}
          strokeWidth={0}
          label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
        />
        <Tooltip
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: 8,
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
