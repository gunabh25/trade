import Link from 'next/link';

import { PricingSection } from '@/features/marketing/components/pricing-section';
import { Layers } from 'lucide-react';

export const metadata = {
  title: 'Pricing — TradeFlow AI',
  description: 'TradeFlow AI plans for paper trading, copy trading, and enterprise scale.',
};

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[#05070a] text-white">
      <header className="border-b border-white/[0.06] bg-[#05070a]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/15 ring-1 ring-indigo-500/30">
              <Layers className="h-4 w-4 text-indigo-300" />
            </div>
            <span className="text-sm font-semibold tracking-tight text-white">TradeFlow AI</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm text-zinc-400 hover:text-white">
              Login
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main>
        <PricingSection />
      </main>
    </div>
  );
}
