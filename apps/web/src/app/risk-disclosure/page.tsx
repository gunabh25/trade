import { LegalDocumentLayout } from '@/features/legal/components/legal-document-layout';

export const metadata = {
  title: 'Risk Disclosure — TradeFlow AI',
  description: 'Trading risk disclosure for TradeFlow AI users.',
};

export default function RiskDisclosurePage() {
  return (
    <LegalDocumentLayout title="Risk Disclosure" updated="July 2, 2026">
      <p>
        <strong>Important:</strong> Trading futures, options, forex, crypto, and other leveraged
        instruments involves substantial risk and is not suitable for every investor.
      </p>

      <h2>1. No guarantee of performance</h2>
      <p>
        Past performance, paper trading results, backtests, and simulated copy fills do not
        guarantee future results. Slippage, latency, partial fills, and broker rejections can
        materially affect live outcomes.
      </p>

      <h2>2. Copy trading risks</h2>
      <ul>
        <li>Follower orders may execute at different prices than the leader.</li>
        <li>Network, API, or platform delays can cause missed or delayed copies.</li>
        <li>Risk rules and kill switches reduce but do not eliminate loss exposure.</li>
        <li>
          You are responsible for sizing, account selection, and enabling/disabling copy groups.
        </li>
      </ul>

      <h2>3. Leverage and loss of capital</h2>
      <p>
        You can lose more than your initial deposit in some markets. Only trade with capital you can
        afford to lose.
      </p>

      <h2>4. Not investment advice</h2>
      <p>
        TradeFlow provides software tools only. We do not recommend specific trades, strategies, or
        leaders. Consult a licensed financial advisor before making investment decisions.
      </p>

      <h2>5. Beta limitations</h2>
      <p>
        During the beta period, features may be incomplete, data may be delayed, and service
        interruptions may occur. Use paper accounts to validate workflows before live trading.
      </p>

      <h2>6. Acknowledgment</h2>
      <p>
        By using TradeFlow, you acknowledge that you understand these risks and accept full
        responsibility for your trading decisions.
      </p>
    </LegalDocumentLayout>
  );
}
