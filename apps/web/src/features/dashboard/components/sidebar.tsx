'use client';

import {
  BarChart3,
  BookOpen,
  Copy,
  CreditCard,
  Key,
  LayoutDashboard,
  LineChart,
  Menu,
  Settings,
  Shield,
  Users,
  Wallet,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import {
  Button,
  ScrollArea,
  Separator,
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
  cn,
} from '@tradeflow/ui';

const navItems = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/accounts', label: 'Accounts', icon: Wallet },
  { href: '/dashboard/copy', label: 'Copy Trading', icon: Copy },
  { href: '/journal', label: 'Journal', icon: BookOpen },
  { href: '/dashboard/analytics', label: 'Analytics', icon: LineChart },
  { href: '/dashboard/risk', label: 'Risk', icon: Shield },
  { href: '/profile', label: 'Profile', icon: Users },
  { href: '/sessions', label: 'Sessions', icon: BarChart3 },
  { href: '/api-keys', label: 'API Keys', icon: Key },
  { href: '/dashboard/billing', label: 'Billing', icon: CreditCard },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-1 px-3">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            {...(onNavigate ? { onClick: onNavigate } : {})}
            className={cn(
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
              isActive
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
  );
}

function SidebarBrand() {
  return (
    <div className="flex h-14 items-center gap-2.5 px-5">
      <div className="bg-primary flex h-7 w-7 items-center justify-center rounded-md">
        <LineChart className="text-primary-foreground h-4 w-4" />
      </div>
      <div>
        <p className="text-sm font-semibold tracking-tight">TradeFlow</p>
        <p className="text-muted-foreground text-[10px] uppercase tracking-widest">Enterprise</p>
      </div>
    </div>
  );
}

export function DashboardSidebar() {
  return (
    <aside className="border-sidebar-border bg-sidebar hidden h-full w-60 flex-col border-r lg:flex">
      <SidebarBrand />
      <Separator className="bg-sidebar-border" />
      <ScrollArea className="flex-1 py-4">
        <NavLinks />
      </ScrollArea>
      <div className="border-sidebar-border border-t p-4">
        <div className="border-sidebar-border bg-sidebar-accent/50 rounded-md border p-3">
          <p className="text-foreground text-xs font-medium">Pro Plan</p>
          <p className="text-muted-foreground mt-0.5 text-[11px]">
            5 accounts · Unlimited copy groups
          </p>
        </div>
      </div>
    </aside>
  );
}

export function MobileSidebarTrigger() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Open navigation</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="border-sidebar-border bg-sidebar w-72 p-0">
        <SheetTitle className="sr-only">Navigation</SheetTitle>
        <SidebarBrand />
        <Separator className="bg-sidebar-border" />
        <ScrollArea className="flex-1 py-4">
          <NavLinks />
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
