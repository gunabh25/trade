export interface AdminOverview {
  total_users: number;
  active_users: number;
  total_subscriptions: number;
  active_subscriptions: number;
  open_tickets: number;
  broker_connections: number;
  broker_errors: number;
  published_announcements: number;
  enabled_feature_flags: number;
}

export interface AdminUser {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  roles: string[];
  created_at: string;
  email_verified: boolean;
}

export interface AdminSubscription {
  id: string;
  user_id: string;
  user_email: string;
  status: string;
  plan_code: string;
  plan_name: string;
  trial_ends_at: string | null;
  current_period_end: string | null;
}

export interface AdminAuditLog {
  id: string;
  user_id: string | null;
  user_email: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  ip_address: string | null;
  created_at: string;
  metadata: Record<string, unknown> | null;
}

export interface AdminSupportTicket {
  id: string;
  user_id: string;
  user_email: string;
  assigned_to_id: string | null;
  subject: string;
  description: string;
  status: string;
  priority: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface AdminBrokerStatus {
  id: string;
  user_id: string;
  user_email: string;
  broker: string;
  name: string;
  status: string;
  last_connected_at: string | null;
  last_error: string | null;
  live_connected: boolean | null;
  live_latency_ms: number | null;
}

export interface FeatureFlag {
  id: string;
  key: string;
  name: string;
  description: string | null;
  enabled: boolean;
  rules: Record<string, unknown> | null;
  updated_at: string;
}

export interface Announcement {
  id: string;
  title: string;
  body: string;
  status: string;
  starts_at: string | null;
  ends_at: string | null;
  target_roles: string[] | null;
  created_at: string;
}

export interface AdminAnalytics {
  users_by_month: Record<string, unknown>[];
  subscriptions_by_plan: { code: string; name: string; count: number }[];
  tickets_by_status: { status: string; count: number }[];
  connections_by_broker: { broker: string; count: number }[];
  mrr_cents: number;
}

export interface AdminHealth {
  status: string;
  environment: string;
  version: string;
  database: Record<string, unknown>;
  redis: Record<string, unknown>;
  broker_monitor: Record<string, unknown>;
  celery: Record<string, unknown>;
}

export interface SystemLog {
  id: string;
  level: string;
  source: string;
  message: string;
  user_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface AdminSearchResult {
  type: string;
  id: string;
  title: string;
  subtitle?: string | null;
}

export interface AdminPermissions {
  roles: string[];
  permissions: Record<string, string[]>;
}

export interface PaginatedMeta {
  page: number;
  pageSize: number;
  total: number;
}
