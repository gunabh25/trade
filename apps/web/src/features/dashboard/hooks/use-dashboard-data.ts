'use client';

import { useEffect, useState } from 'react';

import {
  mockDashboardData,
  type DashboardData,
} from '@/features/dashboard/data/mock-dashboard-data';

interface UseDashboardDataOptions {
  simulateEmpty?: boolean;
  loadingMs?: number;
}

export function useDashboardData(options: UseDashboardDataOptions = {}) {
  const { simulateEmpty = false, loadingMs = 900 } = options;
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEmpty, setIsEmpty] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (simulateEmpty) {
        setIsEmpty(true);
        setData(null);
      } else {
        setData(mockDashboardData);
        setIsEmpty(false);
      }
      setLoading(false);
    }, loadingMs);

    return () => {
      clearTimeout(timer);
    };
  }, [loadingMs, simulateEmpty]);

  return { data, loading, isEmpty };
}
