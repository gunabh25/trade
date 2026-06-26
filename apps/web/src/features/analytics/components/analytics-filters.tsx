'use client';

import { Download, FileText, Loader2 } from 'lucide-react';
import { useState } from 'react';

import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Input,
} from '@tradeflow/ui';

import { downloadAnalyticsExport } from '@/features/analytics/api/analytics-api';
import type { AnalyticsData } from '@/features/analytics/hooks/use-analytics-data';

interface AnalyticsFiltersProps {
  data: AnalyticsData;
}

export function AnalyticsFilters({ data }: AnalyticsFiltersProps) {
  const [exporting, setExporting] = useState<'csv' | 'pdf' | null>(null);

  const handleExport = async (format: 'csv' | 'pdf') => {
    setExporting(format);
    try {
      await downloadAnalyticsExport(format, {
        ...(data.dateFrom ? { date_from: data.dateFrom } : {}),
        ...(data.dateTo ? { date_to: data.dateTo } : {}),
      });
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex flex-wrap gap-2">
        <div>
          <label className="text-muted-foreground mb-1 block text-[10px] font-medium uppercase tracking-wider">
            From
          </label>
          <Input
            type="date"
            value={data.dateFrom}
            onChange={(e) => {
              data.setDateFrom(e.target.value);
            }}
            className="w-[150px]"
          />
        </div>
        <div>
          <label className="text-muted-foreground mb-1 block text-[10px] font-medium uppercase tracking-wider">
            To
          </label>
          <Input
            type="date"
            value={data.dateTo}
            onChange={(e) => {
              data.setDateTo(e.target.value);
            }}
            className="w-[150px]"
          />
        </div>
        {(data.dateFrom || data.dateTo) && (
          <Button
            variant="ghost"
            size="sm"
            className="mt-5"
            onClick={() => {
              data.setDateFrom('');
              data.setDateTo('');
            }}
          >
            Clear
          </Button>
        )}
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-1.5">
            {exporting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Export Report
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => void handleExport('csv')}>
            <FileText className="mr-2 h-4 w-4" />
            Export CSV
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => void handleExport('pdf')}>
            <FileText className="mr-2 h-4 w-4" />
            Export PDF
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
