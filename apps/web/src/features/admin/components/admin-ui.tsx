'use client';

import { Badge, Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';

export function AdminPageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="border-border border-b px-4 py-5 sm:px-6">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      {description ? <p className="text-muted-foreground mt-1 text-sm">{description}</p> : null}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-muted-foreground text-sm font-medium">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
        {hint ? <p className="text-muted-foreground mt-1 text-xs">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}

export function DataTable({
  columns,
  rows,
  emptyMessage = 'No data',
}: {
  columns: string[];
  rows: (string | React.ReactNode)[][];
  emptyMessage?: string;
}) {
  if (rows.length === 0) {
    return <p className="text-muted-foreground py-8 text-center text-sm">{emptyMessage}</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-border border-b">
            {columns.map((col) => (
              <th key={col} className="text-muted-foreground px-3 py-2 text-left font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-border/60 border-b last:border-0">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-3 py-2.5 align-top">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function StatusBadge({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const variant =
    normalized === 'active' ||
    normalized === 'connected' ||
    normalized === 'healthy' ||
    normalized === 'paid' ||
    normalized === 'published'
      ? 'default'
      : normalized === 'error' ||
          normalized === 'past_due' ||
          normalized === 'urgent' ||
          normalized === 'unhealthy'
        ? 'destructive'
        : 'secondary';
  return <Badge variant={variant}>{value.replace(/_/g, ' ')}</Badge>;
}
