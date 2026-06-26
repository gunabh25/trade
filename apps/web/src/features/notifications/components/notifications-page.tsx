'use client';

import { Bell, Settings2 } from 'lucide-react';
import { useState } from 'react';

import { Button, cn } from '@tradeflow/ui';

import { NotificationInbox } from '@/features/notifications/components/notification-inbox';
import { NotificationPreferencesPanel } from '@/features/notifications/components/notification-preferences';

type Tab = 'inbox' | 'preferences';

export function NotificationsPage() {
  const [tab, setTab] = useState<Tab>('inbox');

  return (
    <div className="space-y-6 p-4 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Notifications</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Manage alerts across email, Telegram, Discord, Slack, push, and in-app.
          </p>
        </div>
        <div className="bg-muted inline-flex rounded-lg p-1">
          <Button
            variant="ghost"
            size="sm"
            className={cn(tab === 'inbox' && 'bg-background shadow-sm')}
            onClick={() => {
              setTab('inbox');
            }}
          >
            <Bell className="mr-1.5 h-4 w-4" />
            Inbox
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={cn(tab === 'preferences' && 'bg-background shadow-sm')}
            onClick={() => {
              setTab('preferences');
            }}
          >
            <Settings2 className="mr-1.5 h-4 w-4" />
            Preferences
          </Button>
        </div>
      </div>

      {tab === 'inbox' ? <NotificationInbox /> : <NotificationPreferencesPanel />}
    </div>
  );
}
