'use client';

import { SettingsHubPage } from '@/features/dashboard/components/resource-pages';

const SETTINGS_LINKS = [
  {
    href: '/profile',
    title: 'Profile',
    description: 'Update your name, bio, avatar, and two-factor authentication.',
  },
  {
    href: '/sessions',
    title: 'Sessions',
    description: 'Review active devices and sign out of other sessions.',
  },
  {
    href: '/api-keys',
    title: 'API Keys',
    description: 'Create and revoke programmatic access keys.',
  },
  {
    href: '/dashboard/notifications',
    title: 'Notifications',
    description: 'Configure alerts, digests, and delivery channels.',
  },
  {
    href: '/dashboard/billing',
    title: 'Billing',
    description: 'Manage subscription, invoices, and usage.',
  },
  {
    href: '/dashboard/ai',
    title: 'AI Assistant',
    description: 'Trade assistant, risk advisor, journal coach, and analytics AI.',
  },
];

export default function SettingsPage() {
  return <SettingsHubPage links={SETTINGS_LINKS} />;
}
