import Link from 'next/link';

import { LegalDocumentLayout } from '@/features/legal/components/legal-document-layout';

export const metadata = {
  title: 'Help & FAQ — TradeFlow AI',
  description: 'Getting started with TradeFlow AI paper beta.',
};

export default function HelpPage() {
  return (
    <LegalDocumentLayout title="Help & FAQ" updated="July 2, 2026">
      <h2>Getting started (paper beta)</h2>
      <ol>
        <li>Create an account and sign in.</li>
        <li>
          Go to <strong>Broker</strong> → connect a <strong>Paper</strong> account (recommended for
          beta).
        </li>
        <li>
          Create a <strong>Copy Group</strong> with one leader account and at least one follower
          account.
        </li>
        <li>Start copying, then place a test order on the leader or use Simulate Event.</li>
        <li>Review execution logs, positions, and analytics.</li>
      </ol>

      <h2>Supported brokers</h2>
      <p>
        Paper trading is fully supported for beta validation. Tradovate and Binance connections are
        available but should be tested carefully before live use.
      </p>

      <h2>Known beta limitations</h2>
      <ul>
        <li>Profile avatars may reset on platform redeploy (use object storage in production).</li>
        <li>Email verification and password reset require SMTP configuration.</li>
        <li>AI assistant runs in mock mode unless API keys are configured.</li>
        <li>Billing uses Stripe test/live keys depending on environment configuration.</li>
      </ul>

      <h2>Risk controls</h2>
      <p>
        Configure per-account risk rules under <strong>Risk</strong>. The kill switch immediately
        halts new copy activity for the selected account rule.
      </p>

      <h2>Need help?</h2>
      <p>
        Check <Link href="/status">system status</Link> or email{' '}
        <a href="mailto:support@tradeflow.ai">support@tradeflow.ai</a>.
      </p>
    </LegalDocumentLayout>
  );
}
