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
    <footer className="border-t border-white/[0.06] bg-[#05070a]">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 sm:py-14 md:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr] lg:px-8">
        <div className="md:col-span-2 lg:col-span-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            TradeFlow AI
          </p>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-zinc-500">
            Professional cloud-based trade copier, risk management, and trading analytics — built
            for serious futures and prop firm traders.
          </p>
        </div>

        {FOOTER_COLUMNS.map((column) => (
          <div key={column.title}>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              {column.title}
            </p>
            <ul className="mt-4 space-y-2.5 text-sm text-zinc-500">
              {column.links.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className={cn('transition-colors hover:text-white')}>
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
                    className="transition-colors hover:text-white"
                  >
                    API Docs
                  </a>
                </li>
              ) : null}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-white/[0.06] px-4 py-6 text-center text-xs text-zinc-600 sm:px-6 lg:px-8">
        © {new Date().getFullYear()} TradeFlow AI. All rights reserved.
      </div>
    </footer>
  );
}
