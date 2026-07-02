'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { TooltipProvider } from '@tradeflow/ui';

import { useAuth } from '@/features/auth/components/auth-provider';
import { BetaBanner } from '@/features/dashboard/components/beta-banner';
import { DashboardHeader } from '@/features/dashboard/components/header';
import { DashboardSidebar } from '@/features/dashboard/components/sidebar';
import { useDashboardHeaderData } from '@/features/dashboard/hooks/use-dashboard-header-data';

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const headerData = useDashboardHeaderData(!loading && !!user);

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login');
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="bg-background flex min-h-screen items-center justify-center">
        <div className="border-muted border-t-foreground h-8 w-8 animate-spin rounded-full border-2" />
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="bg-background flex h-dvh overflow-hidden">
        <DashboardSidebar />
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <BetaBanner />
          <DashboardHeader data={headerData} onNotificationsChange={headerData.setNotifications} />
          <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </TooltipProvider>
  );
}

export default DashboardShell;
