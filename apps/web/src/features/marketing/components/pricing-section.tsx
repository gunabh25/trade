'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Check, Loader2, Sparkles } from 'lucide-react';

import type { Plan } from '@tradeflow/types/api';
import { Button, cn } from '@tradeflow/ui';

import { formatPrice, listPlans } from '@/features/billing/api/billing-api';

const FALLBACK_PLANS: Plan[] = [
  {
    id: 'free',
    code: 'free',
    name: 'Free',
    description: 'Paper trading and platform evaluation',
    price_cents: 0,
    currency: 'USD',
    interval: 'month',
    max_trading_accounts: 2,
    max_broker_connections: 2,
    max_copy_groups: 1,
    trial_days: 0,
    features: {
      paper_trading: true,
      copy_trading: true,
      analytics: 'basic',
      support: 'community',
    },
    is_active: true,
  },
  {
    id: 'pro',
    code: 'pro',
    name: 'Pro',
    description: 'Advanced copy trading, risk engine, and analytics',
    price_cents: 7900,
    currency: 'USD',
    interval: 'month',
    max_trading_accounts: 10,
    max_broker_connections: 5,
    max_copy_groups: 5,
    trial_days: 14,
    features: {
      copy_trading: true,
      risk_engine: true,
      analytics: 'advanced',
      support: 'email',
    },
    is_active: true,
  },
  {
    id: 'enterprise',
    code: 'enterprise',
    name: 'Enterprise',
    description: 'Unlimited scale, API access, and priority support',
    price_cents: 19900,
    currency: 'USD',
    interval: 'month',
    max_trading_accounts: 100,
    max_broker_connections: 25,
    max_copy_groups: 50,
    trial_days: 14,
    features: {
      copy_trading: true,
      risk_engine: true,
      analytics: 'enterprise',
      api_access: true,
      support: 'priority',
    },
    is_active: true,
  },
];

function planBullets(plan: Plan): string[] {
  const bullets = [
    `${plan.max_trading_accounts} trading account${plan.max_trading_accounts === 1 ? '' : 's'}`,
    `${plan.max_broker_connections} broker connection${plan.max_broker_connections === 1 ? '' : 's'}`,
    `${plan.max_copy_groups} copy group${plan.max_copy_groups === 1 ? '' : 's'}`,
  ];

  const features = plan.features ?? {};
  for (const [key, value] of Object.entries(features)) {
    if (key === 'support' && typeof value === 'string') {
      bullets.push(`${value.charAt(0).toUpperCase()}${value.slice(1)} support`);
      continue;
    }
    if (key === 'analytics' && typeof value === 'string') {
      bullets.push(`${value.charAt(0).toUpperCase()}${value.slice(1)} analytics`);
      continue;
    }
    if (value === true) {
      bullets.push(key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()));
    }
  }

  return bullets;
}

function PricingCard({ plan, index }: { plan: Plan; index: number }) {
  const isPopular = plan.code === 'pro';
  const isFree = plan.price_cents === 0;
  const bullets = planBullets(plan);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      className={cn(
        'relative flex flex-col rounded-2xl border p-5 sm:p-6 lg:p-8',
        isPopular
          ? 'border-indigo-500/40 bg-gradient-to-b from-indigo-500/[0.08] to-[#0a0d14] shadow-lg shadow-indigo-500/10'
          : 'border-white/[0.06] bg-[#0a0d14]',
      )}
    >
      {isPopular ? (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center gap-1 rounded-full bg-indigo-600 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-white">
            <Sparkles className="h-3 w-3" />
            Most Popular
          </span>
        </div>
      ) : null}

      <div>
        <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
        <p className="mt-1 text-sm text-zinc-500">{plan.description}</p>
      </div>

      <div className="mt-6">
        <span className="text-3xl font-bold tabular-nums text-white sm:text-4xl">
          {formatPrice(plan.price_cents, plan.currency)}
        </span>
        {!isFree ? (
          <span className="text-sm text-zinc-500"> / {plan.interval}</span>
        ) : (
          <span className="text-sm text-zinc-500"> forever</span>
        )}
      </div>

      {plan.trial_days > 0 ? (
        <p className="mt-2 text-sm text-cyan-400">{plan.trial_days}-day free trial included</p>
      ) : null}

      <ul className="mt-8 flex-1 space-y-3">
        {bullets.map((bullet) => (
          <li key={bullet} className="flex items-start gap-2.5 text-sm text-zinc-400">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
            <span className="capitalize">{bullet}</span>
          </li>
        ))}
      </ul>

      <Button
        asChild
        className={cn(
          'mt-8 w-full rounded-lg',
          isPopular
            ? 'bg-indigo-600 text-white hover:bg-indigo-500'
            : 'border-white/10 bg-white/[0.04] text-white hover:bg-white/[0.08]',
        )}
        variant={isPopular ? 'default' : 'outline'}
      >
        <Link href={isFree ? '/register' : '/register'}>
          {isFree ? 'Start Free' : `Start ${plan.name}`}
        </Link>
      </Button>
    </motion.div>
  );
}

export function PricingSection({ showHeading = true }: { showHeading?: boolean }) {
  const [plans, setPlans] = useState<Plan[]>(FALLBACK_PLANS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const live = await listPlans();
        const active = live.filter((plan) => plan.is_active);
        if (active.length > 0) {
          setPlans(active.sort((a, b) => a.price_cents - b.price_cents));
        }
      } catch {
        setPlans(FALLBACK_PLANS);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  return (
    <section id="pricing" className="scroll-mt-16 py-16 sm:scroll-mt-20 sm:py-20 lg:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {showHeading ? (
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
              Simple, Transparent Pricing
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400 sm:mt-4 sm:text-base">
              Start free with paper trading. Upgrade when you are ready to scale copy groups, risk
              controls, and analytics across live broker accounts.
            </p>
          </div>
        ) : null}

        {loading ? (
          <div className="mt-10 flex justify-center text-zinc-500 sm:mt-14">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : (
          <div className="mt-10 grid gap-4 sm:mt-14 sm:gap-6 md:grid-cols-2 xl:grid-cols-3">
            {plans.map((plan, index) => (
              <PricingCard key={plan.id} plan={plan} index={index} />
            ))}
          </div>
        )}

        <p className="mx-auto mt-8 max-w-2xl text-center text-[11px] leading-relaxed text-zinc-600 sm:mt-10 sm:text-xs">
          All plans include secure credential storage, real-time copy execution logs, and risk
          controls. Prices shown in USD. Taxes may apply. See{' '}
          <Link
            href="/terms"
            className="text-zinc-500 underline underline-offset-2 hover:text-white"
          >
            Terms of Service
          </Link>{' '}
          for billing details.
        </p>
      </div>
    </section>
  );
}
