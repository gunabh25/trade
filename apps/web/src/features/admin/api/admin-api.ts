import type {
  AdminAnalytics,
  AdminAuditLog,
  AdminBrokerStatus,
  AdminCreateCouponRequest,
  AdminFailedLogin,
  AdminHealth,
  AdminNotificationDelivery,
  AdminOrganization,
  AdminOverview,
  AdminPermissions,
  AdminPlatformMetrics,
  AdminSearchResult,
  AdminSecurityEvent,
  AdminSubscription,
  AdminSupportTicket,
  AdminTradingAccount,
  AdminUpdatePlanRequest,
  AdminUser,
  Announcement,
  BillingEvent,
  CouponInfo,
  FeatureFlag,
  Invoice,
  PaginatedMeta,
  Plan,
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
  body: {
    plan_code?: string;
    status?: string;
    extend_trial_days?: number;
    cancel_at_period_end?: boolean;
    cancel_immediately?: boolean;
  },
): Promise<AdminSubscription> {
  const response = await apiRequest<AdminSubscription>(`/admin/subscriptions/${subscriptionId}`, {
    method: 'PATCH',
    body,
  });
  return response.data;
}

export async function extendAdminSubscriptionTrial(
  subscriptionId: string,
  days: number,
): Promise<AdminSubscription> {
  return updateAdminSubscription(subscriptionId, { extend_trial_days: days });
}

export async function listAdminCoupons(): Promise<CouponInfo[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/admin/coupons');
  return response.data.map((raw) => ({
    id: toString(raw.id),
    code: toString(raw.code),
    name: toString(raw.name),
    discount_type: toString(raw.discount_type) as CouponInfo['discount_type'],
    percent_off: raw.percent_off != null ? Number(raw.percent_off) : null,
    amount_off_cents: raw.amount_off_cents != null ? Number(raw.amount_off_cents) : null,
    currency: toNullableString(raw.currency),
    duration: toString(raw.duration) as CouponInfo['duration'],
    active: Boolean(raw.active),
    times_redeemed: raw.times_redeemed != null ? Number(raw.times_redeemed) : 0,
    max_redemptions: raw.max_redemptions != null ? Number(raw.max_redemptions) : null,
    expires_at: toNullableString(raw.expires_at),
  }));
}

export async function createAdminCoupon(body: AdminCreateCouponRequest): Promise<CouponInfo> {
  const response = await apiRequest<Record<string, unknown>>('/admin/coupons', {
    method: 'POST',
    body,
  });
  const raw = response.data;
  return {
    id: toString(raw.id),
    code: toString(raw.code),
    name: toString(raw.name),
    discount_type: toString(raw.discount_type) as CouponInfo['discount_type'],
    percent_off: raw.percent_off != null ? Number(raw.percent_off) : null,
    amount_off_cents: raw.amount_off_cents != null ? Number(raw.amount_off_cents) : null,
    currency: toNullableString(raw.currency),
    duration: toString(raw.duration) as CouponInfo['duration'],
    active: Boolean(raw.active),
    expires_at: toNullableString(raw.expires_at),
  };
}

export async function listAdminBillingEvents(): Promise<BillingEvent[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/admin/billing-events');
  return response.data.map((raw) => ({
    id: toString(raw.id),
    event_type: toString(raw.event_type) as BillingEvent['event_type'],
    status: toString(raw.status) as BillingEvent['status'],
    amount_cents: raw.amount_cents != null ? Number(raw.amount_cents) : null,
    currency: toNullableString(raw.currency),
    stripe_invoice_id: toNullableString(raw.stripe_invoice_id),
    created_at: toString(raw.created_at),
  }));
}

export async function listAdminFailedInvoices(): Promise<Invoice[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/admin/invoices/failed');
  return response.data.map((raw) => ({
    id: toString(raw.id),
    stripe_invoice_id: toString(raw.stripe_invoice_id),
    invoice_number: toNullableString(raw.invoice_number),
    status: toString(raw.status) as Invoice['status'],
    amount_due_cents: Number(raw.amount_due_cents ?? 0),
    amount_paid_cents: Number(raw.amount_paid_cents ?? 0),
    currency: toString(raw.currency),
    hosted_invoice_url: toNullableString(raw.hosted_invoice_url),
    invoice_pdf_url: toNullableString(raw.invoice_pdf_url),
    period_start: toNullableString(raw.period_start),
    period_end: toNullableString(raw.period_end),
    paid_at: toNullableString(raw.paid_at),
    created_at: toString(raw.created_at),
  }));
}

export async function listPlans(): Promise<Plan[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/billing/plans');
  return response.data.map((raw) => ({
    id: toString(raw.id),
    code: toString(raw.code),
    name: toString(raw.name),
    description: toNullableString(raw.description),
    price_cents: Number(raw.price_cents ?? 0),
    currency: toString(raw.currency),
    interval: toString(raw.interval) as Plan['interval'],
    max_trading_accounts: Number(raw.max_trading_accounts ?? 0),
    max_broker_connections: Number(raw.max_broker_connections ?? 0),
    max_copy_groups: Number(raw.max_copy_groups ?? 0),
    trial_days: Number(raw.trial_days ?? 0),
    features: (raw.features as Record<string, unknown> | null) ?? null,
    is_active: Boolean(raw.is_active),
    stripe_price_id: toNullableString(raw.stripe_price_id),
  }));
}

export async function updateAdminPlan(
  planCode: string,
  body: AdminUpdatePlanRequest,
): Promise<void> {
  await apiRequest(`/admin/plans/${planCode}`, { method: 'PATCH', body });
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

export async function bulkUserAction(
  userIds: string[],
  action: 'activate' | 'deactivate',
): Promise<{ updated: number }> {
  const response = await apiRequest<{ updated: number }>('/admin/users/bulk', {
    method: 'POST',
    body: { user_ids: userIds, action },
  });
  return response.data;
}

export async function listOrganizations(params?: {
  q?: string;
  page?: number;
}): Promise<{ items: AdminOrganization[]; meta: PaginatedMeta }> {
  const search = new URLSearchParams();
  if (params?.q) search.set('q', params.q);
  if (params?.page) search.set('page', String(params.page));
  const qs = search.toString();
  const response = await apiRequest<{
    items: AdminOrganization[];
    meta: PaginatedMeta;
  }>(`/admin/organizations${qs ? `?${qs}` : ''}`);
  return response.data;
}

export async function createOrganization(body: {
  name: string;
  slug: string;
  plan_code?: string;
  owner_user_id?: string;
}): Promise<AdminOrganization> {
  const response = await apiRequest<AdminOrganization>('/admin/organizations', {
    method: 'POST',
    body,
  });
  return response.data;
}

export async function updateOrganization(
  orgId: string,
  body: { name?: string; plan_code?: string; is_active?: boolean },
): Promise<AdminOrganization> {
  const response = await apiRequest<AdminOrganization>(`/admin/organizations/${orgId}`, {
    method: 'PATCH',
    body,
  });
  return response.data;
}

export async function listTradingAccounts(params?: { q?: string; page?: number }): Promise<{
  items: AdminTradingAccount[];
  meta: PaginatedMeta;
}> {
  const search = new URLSearchParams();
  if (params?.q) search.set('q', params.q);
  if (params?.page) search.set('page', String(params.page));
  const qs = search.toString();
  const response = await apiRequest<{
    items: AdminTradingAccount[];
    meta: PaginatedMeta;
  }>(`/admin/trading-accounts${qs ? `?${qs}` : ''}`);
  return response.data;
}

export async function listNotificationDeliveries(params?: {
  status?: string;
  page?: number;
}): Promise<{
  items: AdminNotificationDelivery[];
  meta: PaginatedMeta;
}> {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.page) search.set('page', String(params.page));
  const qs = search.toString();
  const response = await apiRequest<{
    items: AdminNotificationDelivery[];
    meta: PaginatedMeta;
  }>(`/admin/notifications/deliveries${qs ? `?${qs}` : ''}`);
  return response.data;
}

export async function adminDisconnectBroker(connectionId: string): Promise<AdminBrokerStatus> {
  const response = await apiRequest<AdminBrokerStatus>(
    `/admin/brokers/${connectionId}/disconnect`,
    { method: 'POST' },
  );
  return response.data;
}

export async function getAdminMetrics(): Promise<AdminPlatformMetrics> {
  const response = await apiRequest<AdminPlatformMetrics>('/admin/metrics');
  return response.data;
}

export async function listSecurityEvents(params?: {
  page?: number;
}): Promise<{ items: AdminSecurityEvent[]; meta: PaginatedMeta }> {
  const search = new URLSearchParams();
  if (params?.page) search.set('page', String(params.page));
  const qs = search.toString();
  const response = await apiRequest<{
    items: AdminSecurityEvent[];
    meta: PaginatedMeta;
  }>(`/admin/security/events${qs ? `?${qs}` : ''}`);
  return response.data;
}

export async function listFailedLogins(): Promise<AdminFailedLogin[]> {
  const response = await apiRequest<AdminFailedLogin[]>('/admin/security/failed-logins');
  return response.data;
}
