'use client';

import { Download } from 'lucide-react';

import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input } from '@tradeflow/ui';

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

export function FilterBar({
  value,
  onChange,
  placeholder = 'Search…',
  onSubmit,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onSubmit?: () => void;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <Input
        placeholder={placeholder}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onSubmit?.();
        }}
        className="sm:max-w-xs"
      />
      {onSubmit ? (
        <Button variant="outline" onClick={onSubmit}>
          Filter
        </Button>
      ) : null}
      {children}
    </div>
  );
}

export function ExportCsvButton({
  filename,
  headers,
  rows,
}: {
  filename: string;
  headers: string[];
  rows: string[][];
}) {
  const handleExport = () => {
    const escape = (cell: string) => `"${cell.replace(/"/g, '""')}"`;
    const lines = [headers.map(escape).join(','), ...rows.map((row) => row.map(escape).join(','))];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Button variant="outline" size="sm" onClick={handleExport} disabled={rows.length === 0}>
      <Download className="mr-2 h-4 w-4" />
      Export CSV
    </Button>
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

export function SelectableDataTable<T extends { id: string }>({
  columns,
  items,
  selectedIds,
  onToggle,
  onToggleAll,
  renderRow,
  emptyMessage = 'No data',
}: {
  columns: string[];
  items: T[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  onToggleAll: () => void;
  renderRow: (item: T) => (string | React.ReactNode)[];
  emptyMessage?: string;
}) {
  const allSelected = items.length > 0 && items.every((item) => selectedIds.has(item.id));

  if (items.length === 0) {
    return <p className="text-muted-foreground py-8 text-center text-sm">{emptyMessage}</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-border border-b">
            <th className="w-10 px-3 py-2">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onToggleAll}
                aria-label="Select all"
              />
            </th>
            {columns.map((col) => (
              <th key={col} className="text-muted-foreground px-3 py-2 text-left font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-border/60 border-b last:border-0">
              <td className="px-3 py-2.5">
                <input
                  type="checkbox"
                  checked={selectedIds.has(item.id)}
                  onChange={() => {
                    onToggle(item.id);
                  }}
                  aria-label={`Select ${item.id}`}
                />
              </td>
              {renderRow(item).map((cell, cellIndex) => (
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
    normalized === 'published' ||
    normalized === 'sent'
      ? 'default'
      : normalized === 'error' ||
          normalized === 'past_due' ||
          normalized === 'urgent' ||
          normalized === 'unhealthy' ||
          normalized === 'failed'
        ? 'destructive'
        : 'secondary';
  return <Badge variant={variant}>{value.replace(/_/g, ' ')}</Badge>;
}
