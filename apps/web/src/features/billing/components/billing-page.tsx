'use client';

import { Check, CreditCard, ExternalLink, Sparkles } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import type { BillingOverview, Invoice, Plan } from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Input,
  Skeleton,
} from '@tradeflow/ui';

import {
  createCheckout,
  createPortalSession,
  formatPrice,
  getBillingOverview,
  listInvoices,
  listPlans,
  validateCoupon,
} from '@/features/billing/api/billing-api';
import {
  EmptyState,
  FadeInItem,
  FadeInStagger,
} from '@/features/dashboard/components/motion-primitives';

const METRIC_LABELS: Record<string, string> = {
  trading_accounts: 'Trading accounts',
  broker_connections: 'Broker connections',
  copy_groups: 'Copy groups',
  api_requests: 'API requests',
};

function BillingSkeleton() {
  return (
    <div className="space-y-6 p-4 sm:p-6">
      <Skeleton className="h-8 w-48" />
      <div className="grid gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-72" />
        ))}
      </div>
    </div>
  );
}

function PlanCard({
  plan,
  currentCode,
  onUpgrade,
  loading,
}: {
  plan: Plan;
  currentCode: string;
  onUpgrade: (code: string) => void;
  loading: boolean;
}) {
  const isCurrent = plan.code === currentCode;
  const isFree = plan.price_cents === 0;
  const featureList = Object.entries(plan.features ?? {})
    .map(([key, value]) => {
      if (typeof value === 'boolean') {
        return value ? key.replace(/_/g, ' ') : null;
      }
      return `${key.replace(/_/g, ' ')}: ${String(value)}`;
    })
    .filter(Boolean) as string[];

  return (
    <Card className={plan.code === 'pro' ? 'border-primary shadow-md' : undefined}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{plan.name}</CardTitle>
          {plan.code === 'pro' ? (
            <Badge>
              <Sparkles className="mr-1 h-3 w-3" />
              Popular
            </Badge>
          ) : null}
        </div>
        <CardDescription>{plan.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <span className="text-3xl font-bold">{formatPrice(plan.price_cents, plan.currency)}</span>
          {!isFree ? (
            <span className="text-muted-foreground text-sm"> / {plan.interval}</span>
          ) : null}
        </div>
        {plan.trial_days > 0 && !isCurrent ? (
          <p className="text-muted-foreground text-sm">{plan.trial_days}-day free trial</p>
        ) : null}
        <ul className="space-y-2 text-sm">
          {featureList.map((feature) => (
            <li key={feature} className="flex items-center gap-2">
              <Check className="text-primary h-4 w-4 shrink-0" />
              <span className="capitalize">{feature}</span>
            </li>
          ))}
        </ul>
      </CardContent>
      <CardFooter>
        {isCurrent ? (
          <Button className="w-full" variant="secondary" disabled>
            Current plan
          </Button>
        ) : isFree ? (
          <Button className="w-full" variant="outline" disabled>
            Included
          </Button>
        ) : (
          <Button
            className="w-full"
            onClick={() => {
              onUpgrade(plan.code);
            }}
            disabled={loading}
          >
            Upgrade to {plan.name}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}

export function BillingPage() {
  const [overview, setOverview] = useState<BillingOverview | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [couponCode, setCouponCode] = useState('');
  const [couponMessage, setCouponMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewData, planData, invoiceData] = await Promise.all([
        getBillingOverview(),
        listPlans(),
        listInvoices().catch(() => []),
      ]);
      setOverview(overviewData);
      setPlans(planData);
      setInvoices(invoiceData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load billing');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleUpgrade(planCode: string) {
    setActionLoading(true);
    setCouponMessage(null);
    try {
      if (couponCode.trim()) {
        const coupon = await validateCoupon(couponCode.trim(), planCode);
        setCouponMessage(`Coupon applied: ${coupon.name}`);
      }
      const url = await createCheckout({
        plan_code: planCode,
        coupon_code: couponCode.trim() || null,
      });
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout failed');
      setActionLoading(false);
    }
  }

  async function handleManageBilling() {
    setActionLoading(true);
    try {
      const url = await createPortalSession();
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not open billing portal');
      setActionLoading(false);
    }
  }

  if (loading) {
    return <BillingSkeleton />;
  }

  if (error || !overview) {
    return (
      <div className="p-4 sm:p-6">
        <EmptyState
          icon={CreditCard}
          title="Could not load billing"
          description={error ?? 'Billing data unavailable.'}
          action={
            <Button size="sm" onClick={() => void load()}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  const { subscription } = overview;

  return (
    <div className="space-y-8 p-4 sm:p-6">
      <FadeInItem>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Billing</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Manage your subscription, usage, and invoices.
            </p>
          </div>
          {subscription.plan.code !== 'free' ? (
            <Button
              variant="outline"
              onClick={() => void handleManageBilling()}
              disabled={actionLoading}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Manage subscription
            </Button>
          ) : null}
        </div>
      </FadeInItem>

      <FadeInItem>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Current subscription</CardTitle>
            <CardDescription>
              {subscription.plan.name} plan
              {subscription.is_trialing ? ' — trial active' : ''}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Badge variant={subscription.status === 'active' ? 'default' : 'secondary'}>
              {subscription.status.replace('_', ' ')}
            </Badge>
            {subscription.current_period_end ? (
              <span className="text-muted-foreground text-sm">
                Renews {new Date(subscription.current_period_end).toLocaleDateString()}
              </span>
            ) : null}
            {subscription.trial_ends_at ? (
              <span className="text-muted-foreground text-sm">
                Trial ends {new Date(subscription.trial_ends_at).toLocaleDateString()}
              </span>
            ) : null}
          </CardContent>
        </Card>
      </FadeInItem>

      <FadeInItem>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Usage this period</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {overview.usage.map((item) => (
              <div key={item.metric} className="space-y-1.5">
                <div className="flex justify-between text-sm">
                  <span>{METRIC_LABELS[item.metric] ?? item.metric}</span>
                  <span className="text-muted-foreground">
                    {item.used} / {item.limit}
                  </span>
                </div>
                <div className="bg-muted h-2 overflow-hidden rounded-full">
                  <div
                    className="bg-primary h-full rounded-full transition-all"
                    style={{ width: `${Math.min(item.percent, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </FadeInItem>

      <FadeInItem>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="coupon" className="mb-1 block text-sm font-medium">
              Coupon code
            </label>
            <Input
              id="coupon"
              placeholder="Enter coupon code"
              value={couponCode}
              onChange={(e) => {
                setCouponCode(e.target.value.toUpperCase());
              }}
            />
          </div>
          {couponMessage ? <p className="text-primary text-sm">{couponMessage}</p> : null}
        </div>
      </FadeInItem>

      <FadeInStagger className="grid gap-4 md:grid-cols-3">
        {plans.map((plan) => (
          <FadeInItem key={plan.id}>
            <PlanCard
              plan={plan}
              currentCode={subscription.plan.code}
              onUpgrade={(code) => void handleUpgrade(code)}
              loading={actionLoading}
            />
          </FadeInItem>
        ))}
      </FadeInStagger>

      {invoices.length > 0 ? (
        <FadeInItem>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Invoice history</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="divide-border divide-y">
                {invoices.map((invoice) => (
                  <div key={invoice.id} className="flex items-center justify-between py-3 text-sm">
                    <div>
                      <p className="font-medium">
                        {invoice.invoice_number ?? invoice.stripe_invoice_id.slice(0, 12)}
                      </p>
                      <p className="text-muted-foreground">
                        {new Date(invoice.created_at).toLocaleDateString()} · {invoice.status}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span>{formatPrice(invoice.amount_paid_cents, invoice.currency)}</span>
                      {invoice.hosted_invoice_url ? (
                        <a
                          href={invoice.hosted_invoice_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-primary text-xs hover:underline"
                        >
                          View
                        </a>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </FadeInItem>
      ) : null}
    </div>
  );
}
