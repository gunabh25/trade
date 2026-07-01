'use client';

import { ArrowRight, CheckCircle2, Circle } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Button, Card, CardContent } from '@tradeflow/ui';

import { listCopyGroups } from '@/features/copy/api/copy-api';
import { listBrokerConnections, listTradingAccounts } from '@/features/broker/api/broker-api';

interface OnboardingBannerProps {
  className?: string;
}

export function OnboardingBanner({ className }: OnboardingBannerProps) {
  const [hasConnection, setHasConnection] = useState(false);
  const [hasAccounts, setHasAccounts] = useState(false);
  const [hasCopyGroup, setHasCopyGroup] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      listBrokerConnections().catch(() => []),
      listTradingAccounts().catch(() => []),
      listCopyGroups().catch(() => []),
    ])
      .then(([connections, accounts, groups]) => {
        if (cancelled) return;
        setHasConnection(connections.some((c) => c.status === 'connected'));
        setHasAccounts(accounts.length >= 2);
        setHasCopyGroup(groups.length > 0);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading || (hasConnection && hasAccounts && hasCopyGroup)) {
    return null;
  }

  const steps = [
    {
      done: hasConnection,
      title: 'Connect a broker',
      href: '/dashboard/accounts?connect=1',
      cta: 'Connect',
    },
    {
      done: hasAccounts,
      title: 'Link two trading accounts',
      href: '/dashboard/accounts',
      cta: 'Add account',
    },
    {
      done: hasCopyGroup,
      title: 'Create a copy group',
      href: '/dashboard/copy?create=1',
      cta: 'Set up copy',
    },
  ];

  return (
    <Card className={className}>
      <CardContent className="space-y-4 pt-6">
        <div>
          <p className="font-medium">Get started with TradeFlow</p>
          <p className="text-muted-foreground text-sm">
            Complete these steps to connect brokers and set up copy trading.
          </p>
        </div>
        <ol className="space-y-3">
          {steps.map((step) => (
            <li key={step.title} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm">
                {step.done ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
                ) : (
                  <Circle className="text-muted-foreground h-4 w-4 shrink-0" />
                )}
                <span className={step.done ? 'text-muted-foreground line-through' : ''}>
                  {step.title}
                </span>
              </div>
              {!step.done ? (
                <Button size="sm" variant="outline" asChild>
                  <Link href={step.href}>
                    {step.cta}
                    <ArrowRight className="ml-1 h-3.5 w-3.5" />
                  </Link>
                </Button>
              ) : null}
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
