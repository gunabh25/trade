'use client';

import {
  AlertTriangle,
  Bell,
  CheckCheck,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import type { InAppNotification, NotificationType } from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Skeleton,
  cn,
} from '@tradeflow/ui';

import {
  EmptyState,
  FadeInItem,
  FadeInStagger,
} from '@/features/dashboard/components/motion-primitives';
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/features/notifications/api/notifications-api';
import { formatRelativeTime } from '@/lib/api/normalize';

function iconForType(type: NotificationType) {
  if (type === 'trade_copied' || type === 'copy_failure' || type === 'large_profit') {
    return TrendingUp;
  }
  if (type === 'large_loss' || type === 'kill_switch') {
    return TrendingDown;
  }
  if (type === 'risk_breach' || type === 'position_drift') {
    return AlertTriangle;
  }
  return Bell;
}

function InboxSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-20 w-full" />
      ))}
    </div>
  );
}

export function NotificationInbox() {
  const [items, setItems] = useState<InAppNotification[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listNotifications({ page, pageSize: 15, unreadOnly });
      setItems(response.items);
      setTotalPages(response.meta.totalPages);
      setTotal(response.meta.total);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [page, unreadOnly]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleMarkRead(notification: InAppNotification) {
    if (notification.read) {
      return;
    }
    setItems((prev) =>
      prev.map((item) => (item.id === notification.id ? { ...item, read: true } : item)),
    );
    await markNotificationRead(notification.id).catch(() => undefined);
  }

  async function handleMarkAllRead() {
    setItems((prev) => prev.map((item) => ({ ...item, read: true })));
    await markAllNotificationsRead().catch(() => undefined);
  }

  const unreadCount = items.filter((n) => !n.read).length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle>Inbox</CardTitle>
          <CardDescription>
            {total} notification{total === 1 ? '' : 's'}
            {unreadOnly ? ' (unread only)' : ''}
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant={unreadOnly ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setPage(1);
              setUnreadOnly((value) => !value);
            }}
          >
            Unread only
          </Button>
          <Button variant="outline" size="sm" onClick={() => void handleMarkAllRead()}>
            <CheckCheck className="mr-1.5 h-4 w-4" />
            Mark all read
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <InboxSkeleton />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Bell}
            title="No notifications"
            description={
              unreadOnly
                ? 'You have no unread notifications.'
                : 'Alerts for trades, risk, billing, and system events will appear here.'
            }
          />
        ) : (
          <FadeInStagger className="divide-border divide-y rounded-lg border">
            {items.map((notification) => {
              const Icon = iconForType(notification.type);
              return (
                <FadeInItem key={notification.id}>
                  <div
                    className={cn(
                      'flex gap-4 p-4 transition-colors',
                      !notification.read && 'bg-accent/20',
                    )}
                  >
                    <div className="bg-muted flex h-10 w-10 shrink-0 items-center justify-center rounded-full">
                      <Icon className="text-muted-foreground h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <p className="font-medium">{notification.title}</p>
                          <p className="text-muted-foreground mt-1 text-sm">{notification.body}</p>
                        </div>
                        {!notification.read ? <Badge variant="secondary">New</Badge> : null}
                      </div>
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        <span className="text-muted-foreground text-xs">
                          {formatRelativeTime(notification.created_at)}
                        </span>
                        {!notification.read ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => void handleMarkRead(notification)}
                          >
                            Mark read
                          </Button>
                        ) : null}
                        {notification.action_url ? (
                          <Button variant="ghost" size="sm" className="h-7 text-xs" asChild>
                            <Link href={notification.action_url}>
                              View
                              <ExternalLink className="ml-1 h-3 w-3" />
                            </Link>
                          </Button>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </FadeInItem>
              );
            })}
          </FadeInStagger>
        )}

        {!loading && totalPages > 1 ? (
          <div className="mt-4 flex items-center justify-between">
            <p className="text-muted-foreground text-sm">
              Page {page} of {totalPages}
              {unreadCount > 0 && !unreadOnly ? ` · ${unreadCount} unread on this page` : ''}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => {
                  setPage((p) => p - 1);
                }}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => {
                  setPage((p) => p + 1);
                }}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
