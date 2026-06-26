'use client';

import { AlertTriangle, Bell, CheckCheck, TrendingUp } from 'lucide-react';
import { useState } from 'react';

import {
  Badge,
  Button,
  Popover,
  PopoverContent,
  PopoverTrigger,
  ScrollArea,
  Separator,
  cn,
} from '@tradeflow/ui';

import type { Notification } from '@/features/dashboard/data/mock-dashboard-data';

interface NotificationCenterProps {
  notifications: Notification[];
}

const typeIcons = {
  trade: TrendingUp,
  risk: AlertTriangle,
  system: Bell,
};

export function NotificationCenter({ notifications: initial }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState(initial);
  const unreadCount = notifications.filter((n) => !n.read).length;

  function markAllRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative h-9 w-9">
          <Bell className="h-4 w-4" />
          {unreadCount > 0 ? (
            <span className="bg-primary text-primary-foreground absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-medium">
              {unreadCount}
            </span>
          ) : null}
          <span className="sr-only">Notifications</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <div className="border-border flex items-center justify-between border-b px-4 py-3">
          <div>
            <p className="text-sm font-medium">Notifications</p>
            <p className="text-muted-foreground text-xs">{unreadCount} unread</p>
          </div>
          <Button variant="ghost" size="sm" className="h-8 text-xs" onClick={markAllRead}>
            <CheckCheck className="mr-1 h-3.5 w-3.5" />
            Mark all read
          </Button>
        </div>
        <ScrollArea className="h-[320px]">
          {notifications.length === 0 ? (
            <p className="text-muted-foreground p-6 text-center text-sm">No notifications</p>
          ) : (
            notifications.map((notification) => {
              const Icon = typeIcons[notification.type];
              return (
                <div
                  key={notification.id}
                  className={cn(
                    'border-border/50 flex gap-3 border-b px-4 py-3 last:border-0',
                    !notification.read && 'bg-accent/30',
                  )}
                >
                  <div className="bg-muted mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full">
                    <Icon className="text-muted-foreground h-3.5 w-3.5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium leading-tight">{notification.title}</p>
                      {!notification.read ? (
                        <Badge variant="secondary" className="shrink-0 text-[10px]">
                          New
                        </Badge>
                      ) : null}
                    </div>
                    <p className="text-muted-foreground mt-0.5 text-xs">{notification.message}</p>
                    <p className="text-muted-foreground/70 mt-1 text-[11px]">{notification.time}</p>
                  </div>
                </div>
              );
            })
          )}
        </ScrollArea>
        <Separator />
        <div className="p-2">
          <Button variant="ghost" className="text-muted-foreground w-full text-xs" size="sm">
            View all notifications
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
