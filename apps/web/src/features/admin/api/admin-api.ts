import type {
  AdminAnalytics,
  AdminAuditLog,
  AdminBrokerStatus,
  AdminHealth,
  AdminOverview,
  AdminPermissions,
  AdminSearchResult,
  AdminSubscription,
  AdminSupportTicket,
  AdminUser,
  Announcement,
  FeatureFlag,
  PaginatedMeta,
  SystemLog,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import { toNullableString, toString } from '@/lib/api/normalize';

function normalizeUser(raw: Record<string, unknown>): AdminUser {
  return {
    id: toString(raw.id),
    email: toString(raw.email),
    first_name: toNullableString(raw.first_name),
    last_name: toNullableString(raw.last_name),
    is_active: Boolean(raw.is_active),
    roles: Array.isArray(raw.roles) ? raw.roles.map(String) : [],
    created_at: toString(raw.created_at),
    email_verified: Boolean(raw.email_verified),
  };
}

export async function getAdminOverview(): Promise<AdminOverview> {
  const response = await apiRequest<AdminOverview>('/admin/overview');
  return response.data;
}

export async function adminSearch(
  q: string,
): Promise<{ query: string; results: AdminSearchResult[] }> {
  const response = await apiRequest<{ query: string; results: AdminSearchResult[] }>(
    `/admin/search?q=${encodeURIComponent(q)}`,
  );
  return response.data;
}

export async function listAdminUsers(params?: {
  q?: string;
  page?: number;
}): Promise<{ items: AdminUser[]; meta: PaginatedMeta }> {
  const search = new URLSearchParams();
  if (params?.q) search.set('q', params.q);
  if (params?.page) search.set('page', String(params.page));
  const qs = search.toString();
  const response = await apiRequest<{ items: Record<string, unknown>[]; meta: PaginatedMeta }>(
    `/admin/users${qs ? `?${qs}` : ''}`,
  );
  return {
    items: response.data.items.map((item) => normalizeUser(item)),
    meta: response.data.meta,
  };
}

export async function updateAdminUser(
  userId: string,
  body: { is_active?: boolean; first_name?: string; last_name?: string },
): Promise<AdminUser> {
  const response = await apiRequest<Record<string, unknown>>(`/admin/users/${userId}`, {
    method: 'PATCH',
    body,
  });
  return normalizeUser(response.data);
}

export async function assignUserRole(userId: string, role: string): Promise<AdminUser> {
  const response = await apiRequest<Record<string, unknown>>(`/admin/users/${userId}/roles`, {
    method: 'POST',
    body: { role },
  });
  return normalizeUser(response.data);
}

export async function revokeUserRole(userId: string, role: string): Promise<AdminUser> {
  const response = await apiRequest<Record<string, unknown>>(
    `/admin/users/${userId}/roles/${role}`,
    { method: 'DELETE' },
  );
  return normalizeUser(response.data);
}

export async function getAdminPermissions(): Promise<AdminPermissions> {
  const response = await apiRequest<AdminPermissions>('/admin/permissions');
  return response.data;
}

export async function listAdminSubscriptions(): Promise<AdminSubscription[]> {
  const response = await apiRequest<AdminSubscription[]>('/admin/subscriptions');
  return response.data;
}

export async function listAuditLogs(params?: {
  page?: number;
  action?: string;
}): Promise<{ items: AdminAuditLog[]; meta: PaginatedMeta }> {
  const search = new URLSearchParams();
  if (params?.page) search.set('page', String(params.page));
  if (params?.action) search.set('action', params.action);
  const qs = search.toString();
  const response = await apiRequest<{ items: AdminAuditLog[]; meta: PaginatedMeta }>(
    `/admin/audit-logs${qs ? `?${qs}` : ''}`,
  );
  return response.data;
}

export async function listSupportTickets(): Promise<AdminSupportTicket[]> {
  const response = await apiRequest<AdminSupportTicket[]>('/admin/support-tickets');
  return response.data;
}

export async function updateSupportTicket(
  ticketId: string,
  body: { status?: string; priority?: string },
): Promise<AdminSupportTicket> {
  const response = await apiRequest<AdminSupportTicket>(`/admin/support-tickets/${ticketId}`, {
    method: 'PATCH',
    body,
  });
  return response.data;
}

export async function listBrokerStatus(): Promise<AdminBrokerStatus[]> {
  const response = await apiRequest<AdminBrokerStatus[]>('/admin/brokers/status');
  return response.data;
}

export async function listFeatureFlags(): Promise<FeatureFlag[]> {
  const response = await apiRequest<FeatureFlag[]>('/admin/feature-flags');
  return response.data;
}

export async function toggleFeatureFlag(key: string, enabled: boolean): Promise<FeatureFlag> {
  const response = await apiRequest<FeatureFlag>(`/admin/feature-flags/${key}`, {
    method: 'PATCH',
    body: { enabled },
  });
  return response.data;
}

export async function listAnnouncements(): Promise<Announcement[]> {
  const response = await apiRequest<Announcement[]>('/admin/announcements');
  return response.data;
}

export async function getAdminAnalytics(): Promise<AdminAnalytics> {
  const response = await apiRequest<AdminAnalytics>('/admin/analytics');
  return response.data;
}

export async function getAdminHealth(): Promise<AdminHealth> {
  const response = await apiRequest<AdminHealth>('/admin/health');
  return response.data;
}

export async function listSystemLogs(params?: {
  q?: string;
  page?: number;
}): Promise<{ items: SystemLog[]; meta: PaginatedMeta }> {
  const search = new URLSearchParams();
  if (params?.q) search.set('q', params.q);
  if (params?.page) search.set('page', String(params.page));
  const qs = search.toString();
  const response = await apiRequest<{ items: SystemLog[]; meta: PaginatedMeta }>(
    `/admin/logs${qs ? `?${qs}` : ''}`,
  );
  return response.data;
}

export async function updateAdminSubscription(
  subscriptionId: string,
  body: { plan_code?: string; status?: string; extend_trial_days?: number },
): Promise<AdminSubscription> {
  const response = await apiRequest<AdminSubscription>(`/admin/subscriptions/${subscriptionId}`, {
    method: 'PATCH',
    body,
  });
  return response.data;
}

export async function createFeatureFlag(body: {
  key: string;
  name: string;
  description?: string;
  enabled?: boolean;
}): Promise<FeatureFlag> {
  const response = await apiRequest<FeatureFlag>('/admin/feature-flags', {
    method: 'POST',
    body,
  });
  return response.data;
}

export async function deleteFeatureFlag(key: string): Promise<void> {
  await apiRequest(`/admin/feature-flags/${key}`, { method: 'DELETE' });
}

export async function createAnnouncement(body: {
  title: string;
  body: string;
  status?: string;
  starts_at?: string;
  ends_at?: string;
  target_roles?: string[];
}): Promise<Announcement> {
  const response = await apiRequest<Announcement>('/admin/announcements', {
    method: 'POST',
    body,
  });
  return response.data;
}

export async function updateAnnouncement(
  id: string,
  body: {
    title?: string;
    body?: string;
    status?: string;
    starts_at?: string | null;
    ends_at?: string | null;
    target_roles?: string[] | null;
  },
): Promise<Announcement> {
  const response = await apiRequest<Announcement>(`/admin/announcements/${id}`, {
    method: 'PATCH',
    body,
  });
  return response.data;
}

export async function deleteAnnouncement(id: string): Promise<void> {
  await apiRequest(`/admin/announcements/${id}`, { method: 'DELETE' });
}

export function formatMrr(cents: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
  }).format(cents / 100);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}
