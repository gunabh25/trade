'use client';

import { useCallback, useEffect, useState } from 'react';

import type { BrokerConnection, InAppNotification } from '@tradeflow/types/api';

import { listBrokerConnections } from '@/features/broker/api/broker-api';
import type { Notification, Workspace } from '@/features/dashboard/data/mock-dashboard-data';
import { listNotifications } from '@/features/notifications/api/notifications-api';
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

const EMPTY_CONNECTIONS: BrokerConnection[] = [];

function mapNotificationType(type: InAppNotification['type']): Notification['type'] {
  if (type === 'trade_copied' || type === 'copy_failure') {
    return 'trade';
  }
  if (type === 'risk_breach' || type === 'kill_switch' || type === 'position_drift') {
    return 'risk';
  }
  return 'system';
}

function toHeaderNotification(item: InAppNotification): Notification {
  return {
    id: item.id,
    title: item.title,
    message: item.body,
    time: formatRelativeTime(item.created_at),
    read: item.read,
    type: mapNotificationType(item.type),
  };
}

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

      const notifications = (notificationResponse?.items ?? []).map(toHeaderNotification);

      setData({
        workspaces,
        activeWorkspaceId: workspaces[0]?.id ?? 'default',
        notifications,
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

  return data;
}
