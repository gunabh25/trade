'use client';

import Link from 'next/link';

import { cn } from '@tradeflow/ui';

const FOOTER_COLUMNS = [
  {
    title: 'Product',
    links: [
      { href: '/pricing', label: 'Pricing' },
      { href: '/dashboard', label: 'Dashboard' },
      { href: '/dashboard/analytics', label: 'Analytics' },
      { href: '/dashboard/billing', label: 'Billing' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { href: '/terms', label: 'Terms of Service' },
      { href: '/privacy', label: 'Privacy Policy' },
      { href: '/risk-disclosure', label: 'Risk Disclosure' },
    ],
  },
  {
    title: 'Support',
    links: [
      { href: '/help', label: 'Help & FAQ' },
      { href: '/status', label: 'System Status' },
    ],
  },
] as const;

export function LandingFooter({ apiDocsHref }: { apiDocsHref: string }) {
  return (
    <footer className="border-border bg-background border-t">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 sm:py-14 md:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr] lg:px-8">
        <div className="md:col-span-2 lg:col-span-1">
          <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">
            TradeFlow AI
          </p>
          <p className="text-muted-foreground mt-4 max-w-sm text-sm leading-relaxed">
            Professional cloud-based trade copier, risk management, and trading analytics — built
            for serious futures and prop firm traders.
          </p>
        </div>

        {FOOTER_COLUMNS.map((column) => (
          <div key={column.title}>
            <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">
              {column.title}
            </p>
            <ul className="text-muted-foreground mt-4 space-y-2.5 text-sm">
              {column.links.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className={cn('hover:text-foreground transition-colors')}>
                    {link.label}
                  </Link>
                </li>
              ))}
              {column.title === 'Support' ? (
                <li>
                  <a
                    href={apiDocsHref}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-foreground transition-colors"
                  >
                    API Docs
                  </a>
                </li>
              ) : null}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-border text-muted-foreground border-t px-4 py-6 text-center text-xs sm:px-6 lg:px-8">
        © {new Date().getFullYear()} TradeFlow AI. All rights reserved.
      </div>
    </footer>
  );
}
