'use client';

import { useCallback, useEffect, useState } from 'react';

import type { BrokerConnection, InAppNotification } from '@tradeflow/types/api';

import { listBrokerConnections } from '@/features/broker/api/broker-api';
import type { Workspace } from '@/features/dashboard/data/mock-dashboard-data';
import { listNotifications } from '@/features/notifications/api/notifications-api';

interface DashboardHeaderData {
  workspaces: Workspace[];
  activeWorkspaceId: string;
  notifications: InAppNotification[];
}

const EMPTY_HEADER: DashboardHeaderData = {
  workspaces: [{ id: 'default', name: 'My Portfolio', plan: 'Pro' }],
  activeWorkspaceId: 'default',
  notifications: [],
};

const EMPTY_CONNECTIONS: BrokerConnection[] = [];

export function useDashboardHeaderData(enabled: boolean) {
  const [data, setData] = useState<DashboardHeaderData>(EMPTY_HEADER);

  const load = useCallback(async () => {
    if (!enabled) {
      return;
    }

    try {
      const connections = await listBrokerConnections().catch(
        (): BrokerConnection[] => EMPTY_CONNECTIONS,
      );
      const notificationResponse = await listNotifications({ pageSize: 8 }).catch((): null => null);

      const workspaces: Workspace[] =
        connections.length > 0
          ? connections.map((connection) => ({
              id: connection.id,
              name: connection.name,
              plan: connection.broker === 'paper' ? 'Free' : 'Pro',
            }))
          : EMPTY_HEADER.workspaces;

      setData({
        workspaces,
        activeWorkspaceId: workspaces[0]?.id ?? 'default',
        notifications: notificationResponse?.items ?? [],
      });
    } catch {
      setData(EMPTY_HEADER);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) {
      setData(EMPTY_HEADER);
      return;
    }
    void load();
  }, [enabled, load]);

  return {
    ...data,
    reload: load,
    setNotifications: (notifications: InAppNotification[]) => {
      setData((prev) => ({ ...prev, notifications }));
    },
  };
}
