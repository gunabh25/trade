import { PricingSection } from '@/features/marketing/components/pricing-section';
import { LandingFooter } from '@/features/marketing/components/landing-footer';
import { LandingHeader } from '@/features/marketing/components/landing-header';

export const metadata = {
  title: 'Pricing — TradeFlow AI',
  description: 'TradeFlow AI plans for paper trading, copy trading, and enterprise scale.',
};

function apiDocsHref(): string {
  const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '');
  return base ? `${base}/api/docs` : '/api/health';
}

export default function PricingPage() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-[#05070a] text-white">
      <LandingHeader anchorBase="/" />

      <main>
        <PricingSection />
      </main>

      <LandingFooter apiDocsHref={apiDocsHref()} />
    </div>
  );
}
