'use client';

import { Check, Monitor, Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  cn,
} from '@tradeflow/ui';

const THEME_OPTIONS = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
] as const;

type ThemeValue = (typeof THEME_OPTIONS)[number]['value'];

function ThemeIcon({ theme }: { theme: string | undefined }) {
  if (theme === 'light') {
    return <Sun className="h-4 w-4" />;
  }
  if (theme === 'dark') {
    return <Moon className="h-4 w-4" />;
  }
  return <Monitor className="h-4 w-4" />;
}

interface ThemeToggleProps {
  className?: string;
  align?: 'start' | 'center' | 'end';
  /** Compact icon-only trigger (headers). */
  variant?: 'icon' | 'menu';
}

export function ThemeToggle({ className, align = 'end', variant = 'icon' }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const current = (mounted ? theme : 'system') as ThemeValue | undefined;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size={variant === 'icon' ? 'icon' : 'sm'}
          className={cn(variant === 'icon' ? 'h-9 w-9' : 'h-9 gap-2 px-2', className)}
          aria-label="Toggle theme"
        >
          <ThemeIcon theme={current} />
          {variant === 'menu' ? (
            <span className="text-sm font-medium">
              {THEME_OPTIONS.find((option) => option.value === current)?.label ?? 'Theme'}
            </span>
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="w-40">
        {THEME_OPTIONS.map((option) => {
          const Icon = option.icon;
          const selected = current === option.value;
          return (
            <DropdownMenuItem
              key={option.value}
              onClick={() => {
                setTheme(option.value);
              }}
              className="gap-2"
            >
              <Icon className="h-4 w-4" />
              <span className="flex-1">{option.label}</span>
              {selected ? <Check className="h-4 w-4" /> : null}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/** Inline theme options for menus that already open a dropdown (e.g. user menu). */
export function ThemeMenuItems() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const current = mounted ? theme : 'system';

  return (
    <>
      {THEME_OPTIONS.map((option) => {
        const Icon = option.icon;
        const selected = current === option.value;
        return (
          <DropdownMenuItem
            key={option.value}
            onClick={() => {
              setTheme(option.value);
            }}
            className="gap-2"
          >
            <Icon className="h-4 w-4" />
            <span className="flex-1">{option.label}</span>
            {selected ? <Check className="h-4 w-4" /> : null}
          </DropdownMenuItem>
        );
      })}
    </>
  );
}
