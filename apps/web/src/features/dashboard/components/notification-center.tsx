'use client';

import {
  AlertTriangle,
  Bell,
  CheckCheck,
  ExternalLink,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';

import type { InAppNotification, NotificationType } from '@tradeflow/types/api';

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

import {
  markAllNotificationsRead,
  markNotificationRead,
} from '@/features/notifications/api/notifications-api';
import { formatRelativeTime } from '@/lib/api/normalize';

interface NotificationCenterProps {
  notifications: InAppNotification[];
  onNotificationsChange?: (notifications: InAppNotification[]) => void;
}

function iconForType(type: NotificationType) {
  if (type === 'trade_copied' || type === 'copy_failure' || type === 'large_profit') {
    return TrendingUp;
  }
  if (
    type === 'large_loss' ||
    type === 'risk_breach' ||
    type === 'kill_switch' ||
    type === 'position_drift'
  ) {
    return type === 'large_loss' || type === 'kill_switch' ? TrendingDown : AlertTriangle;
  }
  return Bell;
}

export function NotificationCenter({
  notifications: initial,
  onNotificationsChange,
}: NotificationCenterProps) {
  const router = useRouter();
  const [notifications, setNotifications] = useState(initial);

  const updateNotifications = useCallback(
    (next: InAppNotification[]) => {
      setNotifications(next);
      onNotificationsChange?.(next);
    },
    [onNotificationsChange],
  );

  const unreadCount = notifications.filter((n) => !n.read).length;

  function markAllRead() {
    updateNotifications(notifications.map((n) => ({ ...n, read: true })));
    void markAllNotificationsRead().catch(() => undefined);
  }

  function handleItemClick(notification: InAppNotification) {
    if (!notification.read) {
      const next = notifications.map((n) => (n.id === notification.id ? { ...n, read: true } : n));
      updateNotifications(next);
      void markNotificationRead(notification.id).catch(() => undefined);
    }
    if (notification.action_url) {
      router.push(notification.action_url);
    }
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative h-9 w-9">
          <Bell className="h-4 w-4" />
          {unreadCount > 0 ? (
            <span className="bg-primary text-primary-foreground absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-medium">
              {unreadCount > 9 ? '9+' : unreadCount}
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
              const Icon = iconForType(notification.type);
              return (
                <button
                  key={notification.id}
                  type="button"
                  onClick={() => {
                    handleItemClick(notification);
                  }}
                  className={cn(
                    'border-border/50 hover:bg-accent/40 flex w-full gap-3 border-b px-4 py-3 text-left last:border-0',
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
                    <p className="text-muted-foreground mt-0.5 line-clamp-2 text-xs">
                      {notification.body}
                    </p>
                    <p className="text-muted-foreground/70 mt-1 text-[11px]">
                      {formatRelativeTime(notification.created_at)}
                    </p>
                  </div>
                </button>
              );
            })
          )}
        </ScrollArea>
        <Separator />
        <div className="p-2">
          <Button
            variant="ghost"
            className="text-muted-foreground w-full text-xs"
            size="sm"
            asChild
          >
            <Link href="/dashboard/notifications">
              View all notifications
              <ExternalLink className="ml-1 h-3 w-3" />
            </Link>
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
