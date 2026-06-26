'use client';

import { useCallback, useEffect, useState } from 'react';

import { fetchDashboardData, isDashboardEmpty } from '@/features/dashboard/api/dashboard-api';
import type { DashboardData } from '@/features/dashboard/data/mock-dashboard-data';
import { ApiClientError } from '@/lib/errors';

export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEmpty, setIsEmpty] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await fetchDashboardData();
      setData(next);
      setIsEmpty(isDashboardEmpty(next));
    } catch (err) {
      setData(null);
      setIsEmpty(true);
      setError(err instanceof ApiClientError ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, isEmpty, refetch: load };
}
