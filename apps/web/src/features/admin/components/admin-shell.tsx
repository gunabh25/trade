'use client';

import {
  Activity,
  BarChart3,
  Bell,
  Building2,
  CreditCard,
  FileText,
  Flag,
  Gauge,
  LayoutDashboard,
  LineChart,
  Menu,
  ScrollText,
  Search,
  Server,
  Shield,
  Ticket,
  TrendingUp,
  Users,
  Wallet,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import {
  Button,
  ScrollArea,
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  cn,
} from '@tradeflow/ui';

import { useAuth } from '@/features/auth/components/auth-provider';

const navSections = [
  {
    label: 'Dashboard',
    items: [
      { href: '/admin', label: 'Overview', icon: LayoutDashboard },
      { href: '/admin/search', label: 'Search', icon: Search },
      { href: '/admin/analytics', label: 'Analytics', icon: LineChart },
    ],
  },
  {
    label: 'Manage',
    items: [
      { href: '/admin/users', label: 'Users', icon: Users },
      { href: '/admin/organizations', label: 'Organizations', icon: Building2 },
      { href: '/admin/subscriptions', label: 'Subscriptions', icon: CreditCard },
      { href: '/admin/billing', label: 'Billing', icon: CreditCard },
      { href: '/admin/brokers', label: 'Broker Connections', icon: Wallet },
      { href: '/admin/trading-accounts', label: 'Trading Accounts', icon: TrendingUp },
      { href: '/admin/support', label: 'Support Tickets', icon: Ticket },
      { href: '/admin/notifications', label: 'Notifications', icon: Bell },
      { href: '/admin/feature-flags', label: 'Feature Flags', icon: Flag },
      { href: '/admin/announcements', label: 'Announcements', icon: Bell },
    ],
  },
  {
    label: 'Observability',
    items: [
      { href: '/admin/metrics', label: 'Metrics', icon: Gauge },
      { href: '/admin/security', label: 'Security', icon: Shield },
      { href: '/admin/health', label: 'Server Health', icon: Activity },
      { href: '/admin/audit', label: 'Audit Logs', icon: ScrollText },
      { href: '/admin/logs', label: 'System Logs', icon: FileText },
    ],
  },
  {
    label: 'System',
    items: [{ href: '/admin/permissions', label: 'Permissions', icon: Shield }],
  },
];

function NavContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-4 px-3 py-3">
      {navSections.map((section) => (
        <div key={section.label}>
          <p className="text-muted-foreground mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider">
            {section.label}
          </p>
          <div className="flex flex-col gap-1">
            {section.items.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  {...(onNavigate ? { onClick: onNavigate } : {})}
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
          </div>
        </div>
      ))}
    </nav>
  );
}

export function AdminSidebar() {
  return (
    <aside className="border-border bg-card hidden w-64 shrink-0 border-r md:flex md:flex-col">
      <div className="border-border flex h-14 items-center gap-2 border-b px-5">
        <Server className="text-primary h-5 w-5" />
        <div>
          <p className="text-sm font-semibold">Admin Portal</p>
          <p className="text-muted-foreground text-[11px]">TradeFlow AI</p>
        </div>
      </div>
      <ScrollArea className="flex-1">
        <NavContent />
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
  const [mobileOpen, setMobileOpen] = useState(false);
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
    <div className="bg-background flex min-h-screen flex-col md:flex-row">
      <div className="border-border flex h-14 items-center gap-3 border-b px-4 md:hidden">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon">
              <Menu className="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-0">
            <SheetHeader className="border-border border-b px-5 py-4 text-left">
              <SheetTitle className="flex items-center gap-2">
                <Server className="text-primary h-5 w-5" />
                Admin Portal
              </SheetTitle>
            </SheetHeader>
            <ScrollArea className="h-[calc(100vh-5rem)]">
              <NavContent
                onNavigate={() => {
                  setMobileOpen(false);
                }}
              />
            </ScrollArea>
          </SheetContent>
        </Sheet>
        <p className="text-sm font-semibold">Admin Portal</p>
      </div>

      <AdminSidebar />
      <main className="min-w-0 flex-1 overflow-auto">{children}</main>
    </div>
  );
}
