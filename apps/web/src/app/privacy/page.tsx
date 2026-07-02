import { LegalDocumentLayout } from '@/features/legal/components/legal-document-layout';

export const metadata = {
  title: 'Privacy Policy — TradeFlow AI',
  description: 'Privacy Policy for TradeFlow AI.',
};

export default function PrivacyPage() {
  return (
    <LegalDocumentLayout title="Privacy Policy" updated="July 2, 2026">
      <p>
        This Privacy Policy describes how TradeFlow AI (&quot;TradeFlow,&quot; &quot;we&quot;)
        collects, uses, and protects information when you use our platform.
      </p>

      <h2>1. Information we collect</h2>
      <ul>
        <li>
          <strong>Account data:</strong> name, email, password hash, profile settings, and session
          metadata.
        </li>
        <li>
          <strong>Trading data:</strong> broker connection metadata, account balances, positions,
          orders, copy configuration, risk rules, and execution logs.
        </li>
        <li>
          <strong>Technical data:</strong> IP address, device/browser information, logs, and error
          reports (e.g., Sentry when enabled).
        </li>
      </ul>

      <h2>2. How we use information</h2>
      <ul>
        <li>Provide authentication, copy trading, risk controls, analytics, and support.</li>
        <li>Monitor reliability, security, and abuse prevention.</li>
        <li>Send transactional emails (verification, password reset) when email is configured.</li>
        <li>Improve the product and comply with legal obligations.</li>
      </ul>

      <h2>3. Broker credentials</h2>
      <p>
        Broker API credentials and tokens are stored encrypted at rest. We do not sell your
        credentials. Access is limited to what is required to operate copy trading and account sync
        on your behalf.
      </p>

      <h2>4. Sharing</h2>
      <p>
        We do not sell personal information. We may share data with infrastructure providers
        (hosting, database, email, payments) under contractual safeguards, or when required by law.
      </p>

      <h2>5. Retention</h2>
      <p>
        We retain account and trading records while your account is active and as needed for
        security, audit, and legal compliance. You may request account deletion subject to
        regulatory retention requirements.
      </p>

      <h2>6. Security</h2>
      <p>
        We use industry-standard measures including encryption in transit, encrypted credential
        storage, rate limiting, and access controls. No system is 100% secure.
      </p>

      <h2>7. Your rights</h2>
      <p>
        Depending on your jurisdiction, you may have rights to access, correct, delete, or export
        your data. Contact us to exercise these rights.
      </p>

      <h2>8. Children</h2>
      <p>The service is not intended for users under 18.</p>

      <h2>9. Changes</h2>
      <p>
        We may update this policy. Material changes will be communicated through the product or
        email where appropriate.
      </p>

      <h2>10. Contact</h2>
      <p>
        Privacy inquiries: <a href="mailto:privacy@tradeflow.ai">privacy@tradeflow.ai</a>
      </p>
    </LegalDocumentLayout>
  );
}
