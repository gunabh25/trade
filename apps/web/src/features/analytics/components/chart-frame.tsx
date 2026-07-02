'use client';

import type { ReactElement } from 'react';
import { ResponsiveContainer } from 'recharts';

export function ChartFrame({
  height,
  empty = false,
  emptyMessage = 'No data yet.',
  className,
  children,
}: {
  height: number;
  empty?: boolean;
  emptyMessage?: string;
  className?: string;
  children: ReactElement;
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
    <div className={className ?? 'w-full min-w-0'} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%" debounce={50}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}

export function HeatmapEmptyState({ height, message }: { height: number; message: string }) {
  return (
    <div
      className="text-muted-foreground border-border/60 flex items-center justify-center rounded-md border border-dashed text-center text-sm"
      style={{ height }}
    >
      {message}
    </div>
  );
}
