'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { TooltipProvider } from '@tradeflow/ui';

import { useAuth } from '@/features/auth/components/auth-provider';
import { DashboardHeader } from '@/features/dashboard/components/header';
import { DashboardSidebar } from '@/features/dashboard/components/sidebar';
import { mockDashboardData } from '@/features/dashboard/data/mock-dashboard-data';

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

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
      <div className="bg-background flex min-h-screen">
        <DashboardSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <DashboardHeader
            data={{
              workspaces: mockDashboardData.workspaces,
              activeWorkspaceId: mockDashboardData.activeWorkspaceId,
              notifications: mockDashboardData.notifications,
            }}
          />
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </div>
    </TooltipProvider>
  );
}
