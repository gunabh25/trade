'use client';

import { Button, cn } from '@tradeflow/ui';
import { motion } from 'framer-motion';
import { ArrowRight, Cloud, Shield, Sparkles } from 'lucide-react';
import Link from 'next/link';

import { DashboardPreview } from '@/features/marketing/components/dashboard-preview';
import { Hero3DGraphic } from '@/features/marketing/components/hero-3d-graphic';
import { LandingFooter } from '@/features/marketing/components/landing-footer';
import { LandingHeader } from '@/features/marketing/components/landing-header';
import { PricingSection } from '@/features/marketing/components/pricing-section';

const stats = [
  { value: '50ms', label: 'Avg Copy Latency' },
  { value: '10+', label: 'Broker Integrations' },
  { value: '99.99%', label: 'System Uptime' },
] as const;

const features = [
  {
    icon: Cloud,
    iconClass: 'text-indigo-400 bg-indigo-500/10',
    title: 'Zero Latency Sync',
    description:
      'Mirror master accounts to unlimited followers with sub-50ms routing across futures and prop firm platforms.',
  },
  {
    icon: Shield,
    iconClass: 'text-emerald-400 bg-emerald-500/10',
    title: 'Institutional Risk Controls',
    description:
      'Pre-trade risk gates, position limits, and drawdown rules enforced before every order hits the market.',
  },
  {
    icon: Sparkles,
    iconClass: 'text-cyan-400 bg-cyan-500/10',
    title: 'Cross-Broker Execution',
    description:
      'Unified OMS across Tradovate, Rithmic, and major brokers — one dashboard, every account.',
  },
] as const;

function apiDocsHref(): string {
  const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '');
  return base ? `${base}/api/docs` : '/api/health';
}

export function LandingPage() {
  return (
    <div className="bg-background text-foreground min-h-screen overflow-x-hidden">
      <LandingHeader />

      <main>
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_20%_50%,rgba(99,102,241,0.08)_0%,transparent_50%)]" />

          <div className="mx-auto grid max-w-7xl items-center gap-10 px-4 pb-12 pt-10 sm:gap-12 sm:px-6 sm:pb-16 sm:pt-14 lg:grid-cols-2 lg:gap-8 lg:px-8 lg:pb-24 lg:pt-20">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="mx-auto max-w-xl text-center lg:mx-0 lg:max-w-none lg:text-left"
            >
              <div className="mb-5 inline-flex max-w-full items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-1 sm:mb-6">
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                <span className="text-[10px] font-medium uppercase tracking-wider text-emerald-400 sm:text-[11px]">
                  Live Trading Network Active
                </span>
              </div>

              <h1 className="text-3xl font-bold leading-[1.1] tracking-tight sm:text-4xl md:text-5xl lg:text-[3.25rem]">
                Sync Your{' '}
                <span className="bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">
                  Edge
                </span>
              </h1>

              <p className="text-muted-foreground mx-auto mt-5 max-w-lg text-sm leading-relaxed sm:mt-6 sm:text-base lg:mx-0 lg:text-lg">
                The institutional-grade trade copier for futures and prop firm traders. Mirror
                positions across accounts with real-time risk controls and unified analytics.
              </p>

              <div className="mt-7 flex flex-col gap-3 sm:mt-8 sm:flex-row sm:flex-wrap sm:justify-center lg:justify-start">
                <Button
                  asChild
                  size="lg"
                  className="h-12 w-full rounded-lg bg-indigo-600 px-6 text-white hover:bg-indigo-500 sm:w-auto"
                >
                  <Link href="/register">
                    Get Started
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="border-border bg-muted/40 text-foreground hover:bg-muted/50 h-12 w-full rounded-lg sm:w-auto"
                >
                  <Link href="/dashboard">View Dashboard</Link>
                </Button>
              </div>
            </motion.div>

            <div className="mx-auto w-full max-w-lg lg:max-w-none">
              <Hero3DGraphic />
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="border-border bg-muted/40 border-y">
          <div className="mx-auto grid max-w-7xl grid-cols-1 divide-y divide-white/[0.06] sm:grid-cols-3 sm:divide-x sm:divide-y-0">
            {stats.map((stat) => (
              <div key={stat.label} className="px-4 py-8 text-center sm:px-6 sm:py-10 lg:px-8">
                <p className="text-2xl font-bold tabular-nums text-cyan-400 sm:text-3xl lg:text-4xl">
                  {stat.value}
                </p>
                <p className="text-muted-foreground mt-2 text-[10px] font-medium uppercase tracking-wider sm:text-xs">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section id="features" className="scroll-mt-16 py-16 sm:scroll-mt-20 sm:py-20 lg:py-28">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
                Engineered for Dominance
              </h2>
              <p className="text-muted-foreground mt-3 text-sm leading-relaxed sm:mt-4 sm:text-base">
                Built on a high-performance stack with sub-millisecond routing, enterprise risk
                gates, and multi-broker connectivity for serious trading operations.
              </p>
            </div>

            <div className="mt-10 grid gap-4 sm:mt-14 sm:gap-6 md:grid-cols-2 xl:grid-cols-3">
              {features.map((feature, i) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                  className={cn(
                    'border-border bg-card rounded-2xl border p-5 sm:p-6',
                    i === 2 &&
                      'md:col-span-2 md:max-w-xl md:justify-self-center xl:col-span-1 xl:max-w-none',
                  )}
                >
                  <div
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-lg',
                      feature.iconClass,
                    )}
                  >
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-foreground mt-4 text-base font-semibold sm:mt-5 sm:text-lg">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground mt-2 text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Product preview */}
        <section id="product" className="scroll-mt-16 sm:scroll-mt-20">
          <DashboardPreview />
        </section>

        {/* Pricing */}
        <PricingSection />

        {/* CTA */}
        <section className="pb-16 sm:pb-20 lg:pb-28">
          <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
            <div className="border-border from-card to-background rounded-2xl border bg-gradient-to-b px-5 py-10 text-center sm:px-8 sm:py-12 lg:px-12 lg:py-14">
              <h2 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
                Ready to Scale Your Strategy?
              </h2>
              <p className="text-muted-foreground mx-auto mt-3 max-w-lg text-sm sm:mt-4 sm:text-base">
                Join traders who copy with confidence. Start free, connect your brokers, and scale
                across every account in minutes.
              </p>
              <div className="mt-6 flex flex-col gap-3 sm:mt-8 sm:flex-row sm:flex-wrap sm:justify-center">
                <Button
                  asChild
                  size="lg"
                  className="h-12 w-full rounded-lg bg-indigo-600 px-6 text-white hover:bg-indigo-500 sm:w-auto"
                >
                  <Link href="/register">Create Free Account</Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="border-border text-foreground hover:bg-muted/50 h-12 w-full rounded-lg bg-transparent sm:w-auto"
                >
                  <a href={apiDocsHref()} target="_blank" rel="noopener noreferrer">
                    View API Docs
                  </a>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <LandingFooter apiDocsHref={apiDocsHref()} />
    </div>
  );
}
