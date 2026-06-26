'use client';

import {
  Activity,
  BarChart3,
  Bell,
  CreditCard,
  FileText,
  Flag,
  LayoutDashboard,
  LineChart,
  ScrollText,
  Search,
  Server,
  Shield,
  Ticket,
  Users,
  Wallet,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { Button, ScrollArea, cn } from '@tradeflow/ui';

import { useAuth } from '@/features/auth/components/auth-provider';

const navItems = [
  { href: '/admin', label: 'Overview', icon: LayoutDashboard },
  { href: '/admin/search', label: 'Search', icon: Search },
  { href: '/admin/users', label: 'Users', icon: Users },
  { href: '/admin/subscriptions', label: 'Subscriptions', icon: CreditCard },
  { href: '/admin/audit', label: 'Audit Logs', icon: ScrollText },
  { href: '/admin/support', label: 'Support Tickets', icon: Ticket },
  { href: '/admin/brokers', label: 'Broker Status', icon: Wallet },
  { href: '/admin/feature-flags', label: 'Feature Flags', icon: Flag },
  { href: '/admin/announcements', label: 'Announcements', icon: Bell },
  { href: '/admin/analytics', label: 'Analytics', icon: LineChart },
  { href: '/admin/health', label: 'System Health', icon: Activity },
  { href: '/admin/logs', label: 'Logs', icon: FileText },
  { href: '/admin/permissions', label: 'Permissions', icon: Shield },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="border-border bg-card hidden w-60 shrink-0 border-r md:flex md:flex-col">
      <div className="border-border flex h-14 items-center gap-2 border-b px-5">
        <Server className="text-primary h-5 w-5" />
        <div>
          <p className="text-sm font-semibold">Admin Portal</p>
          <p className="text-muted-foreground text-[11px]">TradeFlow AI</p>
        </div>
      </div>
      <ScrollArea className="flex-1 py-3">
        <nav className="flex flex-col gap-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  active
                    ? 'bg-accent text-foreground'
                    : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground',
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </ScrollArea>
      <div className="border-border border-t p-3">
        <Button variant="outline" size="sm" className="w-full" asChild>
          <Link href="/dashboard">
            <BarChart3 className="mr-2 h-4 w-4" />
            Back to app
          </Link>
        </Button>
      </div>
    </aside>
  );
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const isAdmin = user?.roles.includes('admin') ?? false;

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login');
      return;
    }
    if (!loading && user && !isAdmin) {
      router.replace('/dashboard');
    }
  }, [loading, user, isAdmin, router]);

  if (loading || !user || !isAdmin) {
    return (
      <div className="bg-background flex min-h-screen items-center justify-center">
        <div className="border-muted border-t-foreground h-8 w-8 animate-spin rounded-full border-2" />
      </div>
    );
  }

  return (
    <div className="bg-background flex min-h-screen">
      <AdminSidebar />
      <main className="min-w-0 flex-1 overflow-auto">{children}</main>
    </div>
  );
}
