export type NotificationType =
  | 'trade_copied'
  | 'copy_failure'
  | 'connection_lost'
  | 'risk_breach'
  | 'position_drift'
  | 'kill_switch'
  | 'billing'
  | 'pnl_milestone'
  | 'system';

export type NotificationChannel = 'in_app' | 'email' | 'telegram' | 'discord' | 'slack' | 'push';

export type NotificationEvent =
  | 'trade_copied'
  | 'trade_failed'
  | 'broker_offline'
  | 'risk_alert'
  | 'subscription_expiry'
  | 'pnl_milestone';

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
