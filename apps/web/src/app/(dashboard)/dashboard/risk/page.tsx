'use client';

import { useCallback } from 'react';

import { AsyncListPage } from '@/features/dashboard/components/resource-pages';
import * as riskApi from '@/features/risk/api/risk-api';

export default function RiskPage() {
  const loadItems = useCallback(() => riskApi.listRiskRules(), []);

  return (
    <AsyncListPage
      title="Risk Management"
      description="Active risk rules, limits, and kill-switch status."
      emptyMessage="No risk rules configured. Create rules to monitor exposure and enforce limits."
      loadItems={loadItems}
      getKey={(item) => item.id}
      renderItem={(rule) => (
        <div className="space-y-1">
          <p className="font-medium">{rule.name}</p>
          <p className="text-muted-foreground text-sm">
            {rule.enabled ? 'Enabled' : 'Disabled'}
            {rule.kill_switch_active ? ' · Kill switch active' : ''}
          </p>
          <p className="text-muted-foreground text-xs">
            Daily loss limit:{' '}
            {rule.daily_loss_limit_usd != null ? `$${rule.daily_loss_limit_usd}` : '—'}
            {' · '}
            Max position:{' '}
            {rule.max_position_size_usd != null ? `$${rule.max_position_size_usd}` : '—'}
          </p>
        </div>
      )}
    />
  );
}
