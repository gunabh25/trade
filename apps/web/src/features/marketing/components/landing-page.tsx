'use client';

import { Button, cn } from '@tradeflow/ui';
import { motion } from 'framer-motion';
import { ArrowRight, Cloud, Layers, Shield, Sparkles } from 'lucide-react';
import Link from 'next/link';

import { DashboardPreview } from '@/features/marketing/components/dashboard-preview';
import { Hero3DGraphic } from '@/features/marketing/components/hero-3d-graphic';
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

function LandingHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#05070a]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/15 ring-1 ring-indigo-500/30">
            <Layers className="h-4 w-4 text-indigo-300" />
          </div>
          <span className="text-sm font-semibold tracking-tight text-white">TradeFlow AI</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          <a href="#product" className="text-sm text-zinc-400 transition-colors hover:text-white">
            Product
          </a>
          <a href="#features" className="text-sm text-zinc-400 transition-colors hover:text-white">
            Features
          </a>
          <a href="#pricing" className="text-sm text-zinc-400 transition-colors hover:text-white">
            Pricing
          </a>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden text-sm text-zinc-400 transition-colors hover:text-white sm:inline"
          >
            Login
          </Link>
          <Button asChild className="rounded-lg bg-indigo-600 px-4 text-white hover:bg-indigo-500">
            <Link href="/register">Get Started</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

function HeroGraphic() {
  return <Hero3DGraphic />;
}

function LandingFooter() {
  return (
    <footer className="border-t border-white/[0.06] bg-[#05070a]">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-14 md:grid-cols-[1.4fr_1fr_1fr_1fr] lg:px-8">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/15 ring-1 ring-indigo-500/30">
              <Layers className="h-4 w-4 text-indigo-300" />
            </div>
            <span className="text-sm font-semibold text-white">TradeFlow AI</span>
          </div>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-zinc-500">
            Professional cloud-based trade copier, risk management, and trading analytics — built
            for serious futures and prop firm traders.
          </p>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Product</p>
          <ul className="mt-4 space-y-2.5 text-sm text-zinc-500">
            <li>
              <Link href="/pricing" className="transition-colors hover:text-white">
                Pricing
              </Link>
            </li>
            <li>
              <Link href="/dashboard" className="transition-colors hover:text-white">
                Dashboard
              </Link>
            </li>
            <li>
              <Link href="/dashboard/analytics" className="transition-colors hover:text-white">
                Analytics
              </Link>
            </li>
            <li>
              <Link href="/dashboard/billing" className="transition-colors hover:text-white">
                Billing
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Legal</p>
          <ul className="mt-4 space-y-2.5 text-sm text-zinc-500">
            <li>
              <Link href="/terms" className="transition-colors hover:text-white">
                Terms of Service
              </Link>
            </li>
            <li>
              <Link href="/privacy" className="transition-colors hover:text-white">
                Privacy Policy
              </Link>
            </li>
            <li>
              <Link href="/risk-disclosure" className="transition-colors hover:text-white">
                Risk Disclosure
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Support</p>
          <ul className="mt-4 space-y-2.5 text-sm text-zinc-500">
            <li>
              <a
                href={apiDocsHref()}
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-white"
              >
                API Docs
              </a>
            </li>
            <li>
              <Link href="/status" className="transition-colors hover:text-white">
                System Status
              </Link>
            </li>
            <li>
              <Link href="/help" className="transition-colors hover:text-white">
                Help &amp; FAQ
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-white/[0.06] px-6 py-6 text-center text-xs text-zinc-600 lg:px-8">
        © {new Date().getFullYear()} TradeFlow AI. All rights reserved.
      </div>
    </footer>
  );
}

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#05070a] text-white">
      <LandingHeader />

      <main>
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_20%_50%,rgba(99,102,241,0.08)_0%,transparent_50%)]" />

          <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 pb-16 pt-14 lg:grid-cols-2 lg:gap-8 lg:px-8 lg:pb-24 lg:pt-20">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                <span className="text-[11px] font-medium uppercase tracking-wider text-emerald-400">
                  Live Trading Network Active
                </span>
              </div>

              <h1 className="text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl lg:text-[3.25rem]">
                Sync Your{' '}
                <span className="bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">
                  Edge
                </span>
              </h1>

              <p className="mt-6 max-w-lg text-base leading-relaxed text-zinc-400 sm:text-lg">
                The institutional-grade trade copier for futures and prop firm traders. Mirror
                positions across accounts with real-time risk controls and unified analytics.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Button
                  asChild
                  size="lg"
                  className="rounded-lg bg-indigo-600 px-6 text-white hover:bg-indigo-500"
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
                  className="rounded-lg border-white/10 bg-white/[0.03] text-white hover:bg-white/[0.06]"
                >
                  <Link href="/dashboard">View Dashboard</Link>
                </Button>
              </div>
            </motion.div>

            <HeroGraphic />
          </div>
        </section>

        {/* Stats */}
        <section className="border-y border-white/[0.06] bg-[#060910]">
          <div className="mx-auto grid max-w-7xl grid-cols-1 divide-y divide-white/[0.06] sm:grid-cols-3 sm:divide-x sm:divide-y-0">
            {stats.map((stat) => (
              <div key={stat.label} className="px-6 py-10 text-center lg:px-8">
                <p className="text-3xl font-bold tabular-nums text-cyan-400 sm:text-4xl">
                  {stat.value}
                </p>
                <p className="mt-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section id="features" className="scroll-mt-20 py-20 lg:py-28">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Engineered for Dominance
              </h2>
              <p className="mt-4 text-base leading-relaxed text-zinc-400">
                Built on a high-performance stack with sub-millisecond routing, enterprise risk
                gates, and multi-broker connectivity for serious trading operations.
              </p>
            </div>

            <div className="mt-14 grid gap-6 md:grid-cols-3">
              {features.map((feature, i) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                  className="rounded-2xl border border-white/[0.06] bg-[#0a0d14] p-6"
                >
                  <div
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-lg',
                      feature.iconClass,
                    )}
                  >
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-5 text-lg font-semibold text-white">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-zinc-500">
                    {feature.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Product preview */}
        <section id="product" className="scroll-mt-20 pb-20 lg:pb-28">
          <DashboardPreview />
        </section>

        {/* Pricing */}
        <PricingSection />

        {/* CTA */}
        <section className="pb-20 lg:pb-28">
          <div className="mx-auto max-w-5xl px-6 lg:px-8">
            <div className="rounded-2xl border border-white/[0.08] bg-gradient-to-b from-[#0d1117] to-[#0a0d14] px-8 py-14 text-center sm:px-12">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Ready to Scale Your Strategy?
              </h2>
              <p className="mx-auto mt-4 max-w-lg text-base text-zinc-400">
                Join traders who copy with confidence. Start free, connect your brokers, and scale
                across every account in minutes.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Button
                  asChild
                  size="lg"
                  className="rounded-lg bg-indigo-600 px-6 text-white hover:bg-indigo-500"
                >
                  <Link href="/register">Create Free Account</Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="rounded-lg border-white/10 bg-transparent text-white hover:bg-white/[0.06]"
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

      <LandingFooter />
    </div>
  );
}
