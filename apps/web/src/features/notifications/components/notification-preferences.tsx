'use client';

import { BellOff, Clock, Mail, MessageSquare, Send, Smartphone } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import type {
  NotificationChannel,
  NotificationEvent,
  NotificationPreferences,
  NotificationUserSettings,
} from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Skeleton,
} from '@tradeflow/ui';

import {
  bulkUpdateNotificationPreferences,
  getNotificationPreferences,
  getNotificationSettings,
  updateNotificationChannel,
  updateNotificationSettings,
} from '@/features/notifications/api/notifications-api';

const CHANNEL_META: Record<
  NotificationChannel,
  { label: string; description: string; configKey?: string; configLabel?: string }
> = {
  in_app: { label: 'In-App', description: 'Notification center and bell icon' },
  email: { label: 'Email', description: 'Delivered to your account email' },
  telegram: {
    label: 'Telegram',
    description: 'Direct messages via Telegram bot',
    configKey: 'chat_id',
    configLabel: 'Chat ID',
  },
  discord: {
    label: 'Discord',
    description: 'Webhook posts to a Discord channel',
    configKey: 'webhook_url',
    configLabel: 'Webhook URL',
  },
  slack: {
    label: 'Slack',
    description: 'Webhook posts to a Slack channel',
    configKey: 'webhook_url',
    configLabel: 'Webhook URL',
  },
  push: { label: 'Push', description: 'Browser and mobile push notifications' },
  sms: {
    label: 'SMS',
    description: 'Text messages (architecture ready — provider not configured)',
    configKey: 'phone_number',
    configLabel: 'Phone number',
  },
};

const EXTERNAL_CHANNELS: NotificationChannel[] = [
  'email',
  'telegram',
  'discord',
  'slack',
  'push',
  'sms',
];

function PreferencesSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-40 w-full" />
      <Skeleton className="h-72 w-full" />
    </div>
  );
}

function channelIcon(channel: NotificationChannel) {
  if (channel === 'email') return Mail;
  if (channel === 'telegram' || channel === 'discord' || channel === 'slack') return MessageSquare;
  if (channel === 'push') return Smartphone;
  return Send;
}

export function NotificationPreferencesPanel() {
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null);
  const [settings, setSettings] = useState<NotificationUserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [channelDrafts, setChannelDrafts] = useState<Record<string, string>>({});
  const [preferenceDraft, setPreferenceDraft] = useState<Record<string, Record<string, boolean>>>(
    {},
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [preferences, userSettings] = await Promise.all([
        getNotificationPreferences(),
        getNotificationSettings(),
      ]);
      setPrefs(preferences);
      setSettings(userSettings);

      const drafts: Record<string, string> = {};
      for (const channel of preferences.channels) {
        const meta = CHANNEL_META[channel.channel];
        if (meta.configKey && channel.config?.[meta.configKey]) {
          drafts[channel.channel] = String(channel.config[meta.configKey]);
        }
      }
      setChannelDrafts(drafts);

      const prefMap: Record<string, Record<string, boolean>> = {};
      for (const pref of preferences.preferences) {
        const eventPrefs = prefMap[pref.event_type] ?? {};
        eventPrefs[pref.channel] = pref.enabled;
        prefMap[pref.event_type] = eventPrefs;
      }
      setPreferenceDraft(prefMap);
    } catch {
      setPrefs(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const events = useMemo(() => prefs?.available_events ?? [], [prefs]);

  function isPreferenceEnabled(event: NotificationEvent, channel: NotificationChannel): boolean {
    return preferenceDraft[event]?.[channel] ?? true;
  }

  function togglePreference(event: NotificationEvent, channel: NotificationChannel) {
    setPreferenceDraft((prev) => ({
      ...prev,
      [event]: {
        ...prev[event],
        [channel]: !isPreferenceEnabled(event, channel),
      },
    }));
  }

  async function savePreferences() {
    if (!prefs) return;
    setSaving(true);
    try {
      const updates = events.flatMap((event) =>
        EXTERNAL_CHANNELS.map((channel) => ({
          event_type: event,
          channel,
          enabled: isPreferenceEnabled(event, channel),
        })),
      );
      await bulkUpdateNotificationPreferences({ preferences: updates });
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function saveChannel(channel: NotificationChannel) {
    const meta = CHANNEL_META[channel];
    const config =
      meta.configKey && channelDrafts[channel]
        ? { [meta.configKey]: channelDrafts[channel] }
        : null;
    setSaving(true);
    try {
      await updateNotificationChannel(channel, { enabled: true, config });
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function muteForHours(hours: number) {
    setSaving(true);
    try {
      const next = await updateNotificationSettings({ mute_hours: hours });
      setSettings(next);
    } finally {
      setSaving(false);
    }
  }

  async function clearMute() {
    setSaving(true);
    try {
      const next = await updateNotificationSettings({ clear_mute: true });
      setSettings(next);
    } finally {
      setSaving(false);
    }
  }

  async function toggleDigest(enabled: boolean) {
    setSaving(true);
    try {
      const next = await updateNotificationSettings({ digest_enabled: enabled });
      setSettings(next);
    } finally {
      setSaving(false);
    }
  }

  async function updateDigestFrequency(frequency: 'daily' | 'weekly') {
    setSaving(true);
    try {
      const next = await updateNotificationSettings({ digest_frequency: frequency });
      setSettings(next);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <PreferencesSkeleton />;
  }

  if (!prefs || !settings) {
    return (
      <Card>
        <CardContent className="text-muted-foreground py-10 text-center text-sm">
          Unable to load notification preferences.
        </CardContent>
      </Card>
    );
  }

  const mutedUntil = settings.muted_until ? new Date(settings.muted_until) : null;
  const isMuted = mutedUntil ? mutedUntil.getTime() > Date.now() : false;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BellOff className="h-5 w-5" />
            Mute & Digest
          </CardTitle>
          <CardDescription>
            Pause external alerts temporarily or batch them into a daily digest.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium">Mute external alerts:</span>
            <Button
              variant="outline"
              size="sm"
              disabled={saving}
              onClick={() => void muteForHours(1)}
            >
              1 hour
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={saving}
              onClick={() => void muteForHours(8)}
            >
              8 hours
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={saving}
              onClick={() => void muteForHours(24)}
            >
              24 hours
            </Button>
            {isMuted ? (
              <Button variant="ghost" size="sm" disabled={saving} onClick={() => void clearMute()}>
                Clear mute
              </Button>
            ) : null}
          </div>
          {isMuted && mutedUntil ? (
            <p className="text-muted-foreground text-sm">
              Muted until {mutedUntil.toLocaleString()}
            </p>
          ) : (
            <p className="text-muted-foreground text-sm">External channels are active.</p>
          )}

          <div className="border-border space-y-3 border-t pt-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">Digest mode</p>
                <p className="text-muted-foreground text-xs">
                  Queue external notifications and send a summary instead of instant delivery.
                </p>
              </div>
              <Button
                variant={settings.digest_enabled ? 'default' : 'outline'}
                size="sm"
                disabled={saving}
                onClick={() => void toggleDigest(!settings.digest_enabled)}
              >
                {settings.digest_enabled ? 'Enabled' : 'Disabled'}
              </Button>
            </div>
            {settings.digest_enabled ? (
              <div className="flex flex-wrap items-center gap-2">
                <Clock className="text-muted-foreground h-4 w-4" />
                <Button
                  variant={settings.digest_frequency === 'daily' ? 'default' : 'outline'}
                  size="sm"
                  disabled={saving}
                  onClick={() => void updateDigestFrequency('daily')}
                >
                  Daily
                </Button>
                <Button
                  variant={settings.digest_frequency === 'weekly' ? 'default' : 'outline'}
                  size="sm"
                  disabled={saving}
                  onClick={() => void updateDigestFrequency('weekly')}
                >
                  Weekly (Mondays)
                </Button>
                <span className="text-muted-foreground text-xs">
                  Sent at {settings.digest_hour_utc}:00 UTC
                </span>
              </div>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Channel Configuration</CardTitle>
          <CardDescription>Connect external delivery channels for alerts.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {EXTERNAL_CHANNELS.map((channel) => {
            const meta = CHANNEL_META[channel];
            const Icon = channelIcon(channel);
            const existing = prefs.channels.find((row) => row.channel === channel);
            return (
              <div key={channel} className="border-border rounded-lg border p-4">
                <div className="mb-3 flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Icon className="text-muted-foreground h-4 w-4" />
                    <div>
                      <p className="text-sm font-medium">{meta.label}</p>
                      <p className="text-muted-foreground text-xs">{meta.description}</p>
                    </div>
                  </div>
                  {existing?.enabled ? <Badge variant="secondary">Configured</Badge> : null}
                </div>
                {meta.configKey ? (
                  <div className="space-y-2">
                    <label htmlFor={`channel-${channel}`} className="text-sm font-medium">
                      {meta.configLabel}
                    </label>
                    <Input
                      id={`channel-${channel}`}
                      value={channelDrafts[channel] ?? ''}
                      onChange={(event) => {
                        setChannelDrafts((prev) => ({
                          ...prev,
                          [channel]: event.target.value,
                        }));
                      }}
                      placeholder={meta.configLabel}
                    />
                  </div>
                ) : null}
                <Button
                  className="mt-3"
                  size="sm"
                  variant="outline"
                  disabled={saving}
                  onClick={() => void saveChannel(channel)}
                >
                  Save {meta.label}
                </Button>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Event Preferences</CardTitle>
            <CardDescription>
              Choose which channels receive each alert type. In-app notifications are always on.
            </CardDescription>
          </div>
          <Button size="sm" disabled={saving} onClick={() => void savePreferences()}>
            Save preferences
          </Button>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-border border-b text-left">
                <th className="pb-3 pr-4 font-medium">Event</th>
                {EXTERNAL_CHANNELS.map((channel) => (
                  <th key={channel} className="px-2 pb-3 text-center font-medium">
                    {CHANNEL_META[channel].label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event} className="border-border/60 border-b last:border-0">
                  <td className="py-3 pr-4 font-medium">
                    {prefs.event_labels[event] ?? event.replace(/_/g, ' ')}
                  </td>
                  {EXTERNAL_CHANNELS.map((channel) => {
                    const enabled = isPreferenceEnabled(event, channel);
                    return (
                      <td key={channel} className="px-2 py-3 text-center">
                        <input
                          type="checkbox"
                          checked={enabled}
                          aria-label={`${event} via ${channel}`}
                          className="accent-primary h-4 w-4 cursor-pointer"
                          onChange={() => {
                            togglePreference(event, channel);
                          }}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
