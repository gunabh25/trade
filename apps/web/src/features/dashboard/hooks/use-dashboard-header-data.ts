'use client';

import { useCallback, useEffect, useState } from 'react';

import { listBrokerConnections } from '@/features/broker/api/broker-api';
import type { Notification, Workspace } from '@/features/dashboard/data/mock-dashboard-data';
import { listRiskBreaches } from '@/features/risk/api/risk-api';
import { formatRelativeTime } from '@/lib/api/normalize';

interface DashboardHeaderData {
  workspaces: Workspace[];
  activeWorkspaceId: string;
  notifications: Notification[];
}

const EMPTY_HEADER: DashboardHeaderData = {
  workspaces: [{ id: 'default', name: 'My Portfolio', plan: 'Pro' }],
  activeWorkspaceId: 'default',
  notifications: [],
};

export function useDashboardHeaderData() {
  const [data, setData] = useState<DashboardHeaderData>(EMPTY_HEADER);

  const load = useCallback(async () => {
    try {
      const [connections, breaches] = await Promise.all([
        listBrokerConnections().catch(() => []),
        listRiskBreaches().catch(() => []),
      ]);

      const workspaces: Workspace[] =
        connections.length > 0
          ? connections.map((connection) => ({
              id: connection.id,
              name: connection.name,
              plan: connection.broker === 'paper' ? 'Free' : 'Pro',
            }))
          : EMPTY_HEADER.workspaces;

      const notifications: Notification[] = breaches.slice(0, 8).map((breach) => ({
        id: breach.id,
        title: 'Risk breach detected',
        message: breach.message,
        time: formatRelativeTime(breach.created_at),
        read: false,
        type: 'risk',
      }));

      setData({
        workspaces,
        activeWorkspaceId: workspaces[0]?.id ?? 'default',
        notifications,
      });
    } catch {
      setData(EMPTY_HEADER);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return data;
}
