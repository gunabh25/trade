'use client';

import { LogOut, Settings, User } from 'lucide-react';
import Link from 'next/link';

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@tradeflow/ui';

import { ThemeMenuItems } from '@/components/theme-toggle';
import { useAuth } from '@/features/auth/components/auth-provider';
import { resolveAvatarUrl } from '@/lib/avatar-url';

function getInitials(name: string | null, email: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return `${parts[0]?.[0] ?? ''}${parts[1]?.[0] ?? ''}`.toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}

export function UserMenu() {
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  const displayName = [user.firstName, user.lastName].filter(Boolean).join(' ') || user.email;
  const avatarUrl = resolveAvatarUrl(user.avatarUrl);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-9 gap-2 px-2">
          <Avatar className="h-7 w-7">
            {avatarUrl ? <AvatarImage src={avatarUrl} alt="" /> : null}
            <AvatarFallback className="bg-muted text-xs">
              {getInitials(displayName, user.email)}
            </AvatarFallback>
          </Avatar>
          <span className="hidden max-w-[120px] truncate text-sm font-medium md:inline">
            {displayName}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{displayName}</p>
            <p className="text-muted-foreground text-xs">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/profile">
            <User className="mr-2 h-4 w-4" />
            Profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/dashboard/settings">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="text-muted-foreground text-xs font-normal">
          Theme
        </DropdownMenuLabel>
        <ThemeMenuItems />
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-destructive focus:text-destructive"
          onClick={() => {
            void logout();
          }}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
