import type {
  InAppNotification,
  NotificationChannel,
  NotificationListResponse,
  NotificationPreferences,
  NotificationType,
  UpdateChannelSettingRequest,
  UpdatePreferenceRequest,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import { toNullableString, toNumber, toString } from '@/lib/api/normalize';

function normalizeNotification(raw: Record<string, unknown>): InAppNotification {
  const type = toString(raw.type);
  return {
    id: toString(raw.id),
    type: type as NotificationType,
    title: toString(raw.title),
    body: toString(raw.body),
    read: Boolean(raw.read),
    action_url: toNullableString(raw.action_url),
    metadata: (raw.metadata as Record<string, unknown> | null) ?? null,
    created_at: toString(raw.created_at),
  };
}

export async function listNotifications(params?: {
  unreadOnly?: boolean;
  page?: number;
  pageSize?: number;
}): Promise<NotificationListResponse> {
  const search = new URLSearchParams();
  if (params?.unreadOnly) {
    search.set('unread_only', 'true');
  }
  if (params?.page) {
    search.set('page', String(params.page));
  }
  if (params?.pageSize) {
    search.set('page_size', String(params.pageSize));
  }

  const query = search.toString();
  const path = query ? `/notifications?${query}` : '/notifications';
  const response = await apiRequest<Record<string, unknown>>(path);
  const data = response.data;
  const itemsRaw = Array.isArray(data.items) ? data.items : [];
  const metaRaw = (data.meta as Record<string, unknown> | undefined) ?? {};

  const items = itemsRaw.map((item) => normalizeNotification(item as Record<string, unknown>));

  return {
    items,
    meta: {
      page: toNumber(metaRaw.page, 1),
      pageSize: toNumber(metaRaw.pageSize, 20),
      total: toNumber(metaRaw.total, items.length),
      totalPages: toNumber(metaRaw.totalPages, 1),
    },
  };
}

export async function markNotificationRead(notificationId: string): Promise<InAppNotification> {
  const response = await apiRequest<Record<string, unknown>>(
    `/notifications/${notificationId}/read`,
    { method: 'POST' },
  );
  return normalizeNotification(response.data);
}

export async function markAllNotificationsRead(): Promise<number> {
  const response = await apiRequest<{ updated?: number }>('/notifications/read-all', {
    method: 'POST',
  });
  return toNumber(response.data.updated, 0);
}

export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  const response = await apiRequest<NotificationPreferences>('/notifications/preferences');
  return response.data;
}

export async function updateNotificationChannel(
  channel: NotificationChannel,
  body: UpdateChannelSettingRequest,
): Promise<void> {
  await apiRequest(`/notifications/channels/${channel}`, {
    method: 'PUT',
    body,
  });
}

export async function updateNotificationPreference(body: UpdatePreferenceRequest): Promise<void> {
  await apiRequest('/notifications/preferences', {
    method: 'PUT',
    body,
  });
}
