'use client';

import { useCallback, useEffect, useState } from 'react';

import type { AnalyticsOverview } from '@tradeflow/types/api';

import { getAnalyticsOverview } from '@/features/analytics/api/analytics-api';
import { ApiClientError } from '@/lib/errors';

export function useAnalyticsData() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const overview = await getAnalyticsOverview({
        ...(dateFrom ? { date_from: dateFrom } : {}),
        ...(dateTo ? { date_to: dateTo } : {}),
      });
      setData(overview);
    } catch (err) {
      setData(null);
      setError(err instanceof ApiClientError ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo]);

  useEffect(() => {
    void load();
  }, [load]);

  return {
    data,
    loading,
    error,
    refetch: load,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
  };
}

export type AnalyticsData = ReturnType<typeof useAnalyticsData>;
