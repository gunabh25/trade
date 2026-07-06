'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Layers, Menu, X } from 'lucide-react';

import {
  Button,
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@tradeflow/ui';

import { ThemeToggle } from '@/components/theme-toggle';

const NAV_LINKS = [
  { href: '#product', label: 'Product' },
  { href: '#features', label: 'Features' },
  { href: '#pricing', label: 'Pricing' },
] as const;

export function LandingHeader({ anchorBase = '' }: { anchorBase?: string }) {
  const [open, setOpen] = useState(false);

  return (
    <header className="border-border bg-background/80 sticky top-0 z-50 border-b backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-3 px-4 sm:h-16 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-500/15 ring-1 ring-indigo-500/30">
            <Layers className="h-4 w-4 text-indigo-600 dark:text-indigo-300" />
          </div>
          <span className="text-foreground truncate text-sm font-semibold tracking-tight">
            TradeFlow AI
          </span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex lg:gap-8">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={`${anchorBase}${link.href}`}
              className="text-muted-foreground hover:text-foreground text-sm transition-colors"
            >
              {link.label}
            </a>
          ))}
          <Link
            href="/pricing"
            className="text-muted-foreground hover:text-foreground text-sm transition-colors"
          >
            Plans
          </Link>
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <ThemeToggle />
          <Link
            href="/login"
            className="text-muted-foreground hover:text-foreground hidden text-sm transition-colors sm:inline"
          >
            Login
          </Link>
          <Button
            asChild
            size="sm"
            className="hidden rounded-lg bg-indigo-600 px-3 text-white hover:bg-indigo-500 sm:inline-flex sm:px-4"
          >
            <Link href="/register">Get Started</Link>
          </Button>

          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="md:hidden" aria-label="Open menu">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="sm:max-w-xs">
              <SheetHeader className="text-left">
                <SheetTitle>Menu</SheetTitle>
              </SheetHeader>
              <nav className="mt-8 flex flex-col gap-1">
                {NAV_LINKS.map((link) => (
                  <SheetClose key={link.href} asChild>
                    <a
                      href={`${anchorBase}${link.href}`}
                      className="hover:bg-accent rounded-lg px-3 py-3 text-base transition-colors"
                      onClick={() => {
                        setOpen(false);
                      }}
                    >
                      {link.label}
                    </a>
                  </SheetClose>
                ))}
                <SheetClose asChild>
                  <Link
                    href="/pricing"
                    className="hover:bg-accent rounded-lg px-3 py-3 text-base transition-colors"
                  >
                    Plans
                  </Link>
                </SheetClose>
                <SheetClose asChild>
                  <Link
                    href="/login"
                    className="hover:bg-accent rounded-lg px-3 py-3 text-base transition-colors"
                  >
                    Login
                  </Link>
                </SheetClose>
              </nav>
              <div className="mt-6 space-y-3">
                <div className="flex items-center justify-between px-1">
                  <span className="text-muted-foreground text-sm">Theme</span>
                  <ThemeToggle />
                </div>
                <SheetClose asChild>
                  <Button asChild className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500">
                    <Link href="/register">Get Started</Link>
                  </Button>
                </SheetClose>
              </div>
              <SheetClose className="ring-offset-background absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100">
                <X className="h-4 w-4" />
                <span className="sr-only">Close</span>
              </SheetClose>
            </SheetContent>
          </Sheet>

          <Button
            asChild
            size="sm"
            className="rounded-lg bg-indigo-600 px-3 text-white hover:bg-indigo-500 sm:hidden"
          >
            <Link href="/register">Start</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
