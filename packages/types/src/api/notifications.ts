export type NotificationType =
  | 'trade_copied'
  | 'copy_failure'
  | 'connection_lost'
  | 'risk_breach'
  | 'position_drift'
  | 'kill_switch'
  | 'billing'
  | 'pnl_milestone'
  | 'large_profit'
  | 'large_loss'
  | 'user_invitation'
  | 'password_changed'
  | 'system';

export type NotificationChannel =
  | 'in_app'
  | 'email'
  | 'telegram'
  | 'discord'
  | 'slack'
  | 'push'
  | 'sms';

export type NotificationEvent =
  | 'trade_copied'
  | 'trade_failed'
  | 'broker_offline'
  | 'risk_alert'
  | 'subscription_expiry'
  | 'pnl_milestone'
  | 'large_profit'
  | 'large_loss'
  | 'system_maintenance'
  | 'user_invitation'
  | 'password_changed';

export interface InAppNotification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  read: boolean;
  action_url: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: InAppNotification[];
  meta: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

export interface NotificationChannelSetting {
  channel: NotificationChannel;
  enabled: boolean;
  config: Record<string, unknown> | null;
}

export interface NotificationPreference {
  event_type: NotificationEvent;
  channel: NotificationChannel;
  enabled: boolean;
}

export interface NotificationPreferences {
  channels: NotificationChannelSetting[];
  preferences: NotificationPreference[];
  available_events: NotificationEvent[];
  available_channels: NotificationChannel[];
  event_labels: Record<string, string>;
}

export interface NotificationUserSettings {
  muted_until: string | null;
  digest_enabled: boolean;
  digest_frequency: 'daily' | 'weekly';
  digest_hour_utc: number;
}

export interface UpdateChannelSettingRequest {
  enabled: boolean;
  config?: Record<string, unknown> | null;
}

export interface UpdatePreferenceRequest {
  event_type: NotificationEvent;
  channel: NotificationChannel;
  enabled: boolean;
}

export interface BulkUpdatePreferencesRequest {
  preferences: UpdatePreferenceRequest[];
}

export interface UpdateNotificationUserSettingsRequest {
  muted_until?: string | null;
  mute_hours?: number;
  clear_mute?: boolean;
  digest_enabled?: boolean;
  digest_frequency?: 'daily' | 'weekly';
  digest_hour_utc?: number;
}

export interface UnreadCountResponse {
  count: number;
}
