import { LegalDocumentLayout } from '@/features/legal/components/legal-document-layout';

export const metadata = {
  title: 'Terms of Service — TradeFlow AI',
  description: 'Terms of Service for TradeFlow AI paper trading platform.',
};

export default function TermsPage() {
  return (
    <LegalDocumentLayout title="Terms of Service" updated="July 2, 2026">
      <p>
        These Terms of Service (&quot;Terms&quot;) govern your access to and use of TradeFlow AI
        (&quot;TradeFlow,&quot; &quot;we,&quot; &quot;us&quot;). By creating an account or using the
        service, you agree to these Terms.
      </p>

      <h2>1. Beta program</h2>
      <p>
        TradeFlow is currently offered as a <strong>controlled beta</strong>. Features,
        availability, and performance may change without notice. The service is provided for
        evaluation and paper trading purposes unless explicitly stated otherwise.
      </p>

      <h2>2. Eligibility</h2>
      <p>
        You must be at least 18 years old and legally able to enter into these Terms. You are
        responsible for maintaining the confidentiality of your account credentials.
      </p>

      <h2>3. Paper trading</h2>
      <p>
        Unless you explicitly connect a live brokerage account and enable live copy trading, orders
        executed through paper accounts are simulated. Paper results do not guarantee live trading
        performance.
      </p>

      <h2>4. Acceptable use</h2>
      <ul>
        <li>Do not attempt to disrupt, reverse engineer, or abuse the platform.</li>
        <li>Do not use the service for unlawful activity or market manipulation.</li>
        <li>Do not share access credentials or circumvent rate limits or security controls.</li>
      </ul>

      <h2>5. Broker connections</h2>
      <p>
        When you connect a third-party broker, you authorize TradeFlow to access account data and
        submit orders according to your configured copy and risk settings. You remain responsible
        for all trading activity in your brokerage accounts.
      </p>

      <h2>6. Fees and billing</h2>
      <p>
        Paid plans, trials, and billing terms are presented in the product at checkout. We may
        change pricing with reasonable notice. Taxes may apply where required by law.
      </p>

      <h2>7. Disclaimers</h2>
      <p>
        THE SERVICE IS PROVIDED &quot;AS IS&quot; WITHOUT WARRANTIES OF ANY KIND. TRADEFLOW DOES NOT
        PROVIDE INVESTMENT, TAX, OR LEGAL ADVICE. TRADING INVOLVES SUBSTANTIAL RISK OF LOSS.
      </p>

      <h2>8. Limitation of liability</h2>
      <p>
        TO THE MAXIMUM EXTENT PERMITTED BY LAW, TRADEFLOW SHALL NOT BE LIABLE FOR INDIRECT,
        INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR FOR TRADING LOSSES ARISING FROM
        USE OF THE SERVICE, COPY LATENCY, BROKER OUTAGES, OR DATA INACCURACIES.
      </p>

      <h2>9. Termination</h2>
      <p>
        You may stop using the service at any time. We may suspend or terminate access for
        violations of these Terms or to protect platform integrity.
      </p>

      <h2>10. Contact</h2>
      <p>
        Questions about these Terms: <a href="mailto:legal@tradeflow.ai">legal@tradeflow.ai</a>
      </p>
    </LegalDocumentLayout>
  );
}
