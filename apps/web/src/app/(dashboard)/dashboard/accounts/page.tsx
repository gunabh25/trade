'use client';

import { useCallback } from 'react';

import * as brokerApi from '@/features/broker/api/broker-api';
import { AsyncListPage } from '@/features/dashboard/components/resource-pages';

export default function AccountsPage() {
  const loadItems = useCallback(() => brokerApi.listBrokerConnections(), []);

  return (
    <AsyncListPage
      title="Trading Accounts"
      description="Broker connections and linked trading accounts."
      emptyMessage="No broker connections yet. Connect a broker from the API or admin portal."
      loadItems={loadItems}
      getKey={(item) => item.id}
      renderItem={(connection) => (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="font-medium">{connection.name}</p>
            <p className="text-muted-foreground text-sm">
              {connection.broker} · {connection.status}
            </p>
          </div>
          {connection.last_connected_at ? (
            <p className="text-muted-foreground text-xs">
              Last connected {new Date(connection.last_connected_at).toLocaleString()}
            </p>
          ) : null}
        </div>
      )}
    />
  );
}
