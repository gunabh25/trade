'use client';

import { Search } from 'lucide-react';
import { usePathname } from 'next/navigation';

import { Input, Separator } from '@tradeflow/ui';

import { NotificationCenter } from '@/features/dashboard/components/notification-center';
import { MobileSidebarTrigger } from '@/features/dashboard/components/sidebar';
import { UserMenu } from '@/features/dashboard/components/user-menu';
import {
  HeaderBreadcrumb,
  WorkspaceSwitcher,
} from '@/features/dashboard/components/workspace-switcher';

import type { DashboardData } from '@/features/dashboard/data/mock-dashboard-data';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Overview',
  '/dashboard/analytics': 'Analytics',
  '/journal': 'Journal',
  '/profile': 'Profile',
  '/sessions': 'Sessions',
  '/api-keys': 'API Keys',
};

interface DashboardHeaderProps {
  data: Pick<DashboardData, 'workspaces' | 'activeWorkspaceId' | 'notifications'>;
}

export function DashboardHeader({ data }: DashboardHeaderProps) {
  const pathname = usePathname();
  const title = pageTitles[pathname] ?? 'Overview';

  return (
    <header className="border-border bg-background/80 sticky top-0 z-40 flex h-14 shrink-0 items-center gap-4 border-b px-4 backdrop-blur-xl sm:px-6">
      <MobileSidebarTrigger />
      <WorkspaceSwitcher workspaces={data.workspaces} activeWorkspaceId={data.activeWorkspaceId} />
      <Separator orientation="vertical" className="hidden h-6 sm:block" />
      <HeaderBreadcrumb title={title} />

      <div className="ml-auto flex items-center gap-2">
        <div className="relative hidden md:block">
          <Search className="text-muted-foreground absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2" />
          <Input
            placeholder="Search symbols, accounts…"
            className="border-border/60 bg-muted/30 h-9 w-56 pl-9 text-sm"
          />
        </div>
        <NotificationCenter notifications={data.notifications} />
        <UserMenu />
      </div>
    </header>
  );
}
