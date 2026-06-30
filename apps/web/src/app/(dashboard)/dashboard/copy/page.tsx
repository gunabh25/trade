'use client';

import { useCallback } from 'react';

import * as copyApi from '@/features/copy/api/copy-api';
import { AsyncListPage } from '@/features/dashboard/components/resource-pages';

export default function CopyTradingPage() {
  const loadItems = useCallback(() => copyApi.listCopyGroups(), []);

  return (
    <AsyncListPage
      title="Copy Trading"
      description="Leader/follower copy groups and replication status."
      emptyMessage="No copy groups configured. Create a group via the API to start copying."
      loadItems={loadItems}
      getKey={(item) => item.id}
      renderItem={(group) => (
        <div className="space-y-1">
          <p className="font-medium">{group.name}</p>
          <p className="text-muted-foreground text-sm">
            {group.mode} · {group.status} · {group.followers.length} follower
            {group.followers.length === 1 ? '' : 's'}
          </p>
          <p className="text-muted-foreground text-xs">
            Copying {group.copying_enabled ? 'enabled' : 'disabled'}
            {group.sim_validated ? ' · Sim validated' : ''}
          </p>
        </div>
      )}
    />
  );
}
