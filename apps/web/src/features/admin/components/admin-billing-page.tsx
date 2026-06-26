'use client';

import { CreditCard } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import type {
  AdminCreateCouponRequest,
  AdminSubscription,
  AdminUpdatePlanRequest,
  BillingEvent,
  CouponInfo,
  Invoice,
  Plan,
} from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Skeleton,
} from '@tradeflow/ui';

import {
  createAdminCoupon,
  extendAdminSubscriptionTrial,
  listAdminBillingEvents,
  listAdminCoupons,
  listAdminFailedInvoices,
  listAdminSubscriptions,
  listPlans,
  updateAdminPlan,
  updateAdminSubscription,
} from '@/features/admin/api/admin-api';
import { AdminPageHeader, DataTable, StatusBadge } from '@/features/admin/components/admin-ui';
import { formatPrice } from '@/features/billing/api/billing-api';
import { EmptyState } from '@/features/dashboard/components/motion-primitives';

type Tab = 'subscriptions' | 'coupons' | 'plans' | 'events' | 'invoices';

function LoadingBlock() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

export function AdminBillingPage() {
  const [tab, setTab] = useState<Tab>('subscriptions');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [subscriptions, setSubscriptions] = useState<AdminSubscription[]>([]);
  const [coupons, setCoupons] = useState<CouponInfo[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [events, setEvents] = useState<BillingEvent[]>([]);
  const [failedInvoices, setFailedInvoices] = useState<Invoice[]>([]);

  const [couponForm, setCouponForm] = useState<AdminCreateCouponRequest>({
    code: '',
    name: '',
    discount_type: 'percent',
    percent_off: 20,
    duration: 'once',
  });
  const [planDrafts, setPlanDrafts] = useState<Record<string, AdminUpdatePlanRequest>>({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [subs, couponRows, planRows, eventRows, invoiceRows] = await Promise.all([
        listAdminSubscriptions(),
        listAdminCoupons(),
        listPlans(),
        listAdminBillingEvents(),
        listAdminFailedInvoices(),
      ]);
      setSubscriptions(subs);
      setCoupons(couponRows);
      setPlans(planRows);
      setEvents(eventRows);
      setFailedInvoices(invoiceRows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load billing admin data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCancel(sub: AdminSubscription) {
    await updateAdminSubscription(sub.id, { status: 'canceled', cancel_immediately: true });
    void load();
  }

  async function handleExtendTrial(sub: AdminSubscription) {
    await extendAdminSubscriptionTrial(sub.id, 7);
    void load();
  }

  async function handleCreateCoupon() {
    await createAdminCoupon(couponForm);
    setCouponForm({
      code: '',
      name: '',
      discount_type: 'percent',
      percent_off: 20,
      duration: 'once',
    });
    void load();
  }

  async function handleSavePlan(plan: Plan) {
    const draft = planDrafts[plan.code] ?? {};
    await updateAdminPlan(plan.code, draft);
    void load();
  }

  if (loading) return <LoadingBlock />;
  if (error) {
    return (
      <EmptyState
        icon={CreditCard}
        title="Billing admin unavailable"
        description={error}
        action={
          <Button size="sm" onClick={() => void load()}>
            Retry
          </Button>
        }
      />
    );
  }

  return (
    <div>
      <AdminPageHeader
        title="Billing"
        description="Subscriptions, coupons, plans, webhooks, and failed payments."
      />
      <div className="space-y-4 p-4 sm:p-6">
        <div className="bg-muted inline-flex rounded-lg p-1">
          {(['subscriptions', 'coupons', 'plans', 'events', 'invoices'] as Tab[]).map((item) => (
            <Button
              key={item}
              size="sm"
              variant={tab === item ? 'default' : 'ghost'}
              onClick={() => {
                setTab(item);
              }}
            >
              {item.charAt(0).toUpperCase() + item.slice(1)}
            </Button>
          ))}
        </div>

        {tab === 'subscriptions' ? (
          <Card>
            <CardContent className="pt-6">
              <DataTable
                columns={['User', 'Plan', 'Status', 'Trial ends', 'Period end', 'Actions']}
                rows={subscriptions.map((sub) => [
                  sub.user_email,
                  sub.plan_name,
                  <StatusBadge key="status" value={sub.status} />,
                  sub.trial_ends_at ? new Date(sub.trial_ends_at).toLocaleDateString() : '—',
                  sub.current_period_end
                    ? new Date(sub.current_period_end).toLocaleDateString()
                    : '—',
                  sub.status !== 'canceled' ? (
                    <div key="actions" className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => void handleExtendTrial(sub)}
                      >
                        +7d trial
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => void handleCancel(sub)}>
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    '—'
                  ),
                ])}
                emptyMessage="No subscriptions"
              />
            </CardContent>
          </Card>
        ) : null}

        {tab === 'coupons' ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Create coupon</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="Code (e.g. LAUNCH20)"
                  value={couponForm.code}
                  onChange={(e) => {
                    setCouponForm((prev) => ({ ...prev, code: e.target.value.toUpperCase() }));
                  }}
                />
                <Input
                  placeholder="Display name"
                  value={couponForm.name}
                  onChange={(e) => {
                    setCouponForm((prev) => ({ ...prev, name: e.target.value }));
                  }}
                />
                <Input
                  type="number"
                  placeholder="Percent off"
                  value={couponForm.percent_off ?? ''}
                  onChange={(e) => {
                    setCouponForm((prev) => ({ ...prev, percent_off: Number(e.target.value) }));
                  }}
                />
                <Button
                  onClick={() => void handleCreateCoupon()}
                  disabled={!couponForm.code || !couponForm.name}
                >
                  Create coupon
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Active coupons</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable
                  columns={['Code', 'Discount', 'Redeemed', 'Status']}
                  rows={coupons.map((coupon) => [
                    coupon.code,
                    coupon.percent_off
                      ? `${coupon.percent_off}%`
                      : formatPrice(coupon.amount_off_cents ?? 0),
                    `${coupon.times_redeemed ?? 0}${coupon.max_redemptions ? ` / ${coupon.max_redemptions}` : ''}`,
                    <Badge key="status" variant={coupon.active ? 'default' : 'secondary'}>
                      {coupon.active ? 'Active' : 'Inactive'}
                    </Badge>,
                  ])}
                  emptyMessage="No coupons"
                />
              </CardContent>
            </Card>
          </div>
        ) : null}

        {tab === 'plans' ? (
          <div className="grid gap-4 md:grid-cols-3">
            {plans.map((plan) => (
              <Card key={plan.id}>
                <CardHeader>
                  <CardTitle className="text-base">{plan.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Input
                    placeholder="Stripe price ID"
                    defaultValue={plan.stripe_price_id ?? ''}
                    onChange={(e) => {
                      setPlanDrafts((prev) => ({
                        ...prev,
                        [plan.code]: { ...prev[plan.code], stripe_price_id: e.target.value },
                      }));
                    }}
                  />
                  <Input
                    placeholder="Stripe product ID"
                    defaultValue=""
                    onChange={(e) => {
                      setPlanDrafts((prev) => ({
                        ...prev,
                        [plan.code]: { ...prev[plan.code], stripe_product_id: e.target.value },
                      }));
                    }}
                  />
                  <Button size="sm" variant="outline" onClick={() => void handleSavePlan(plan)}>
                    Save Stripe IDs
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : null}

        {tab === 'events' ? (
          <Card>
            <CardContent className="pt-6">
              <DataTable
                columns={['Event', 'Status', 'Amount', 'When']}
                rows={events.map((event) => [
                  event.event_type.replace(/_/g, ' '),
                  event.status,
                  event.amount_cents != null
                    ? formatPrice(event.amount_cents, event.currency ?? 'USD')
                    : '—',
                  new Date(event.created_at).toLocaleString(),
                ])}
                emptyMessage="No billing events"
              />
            </CardContent>
          </Card>
        ) : null}

        {tab === 'invoices' ? (
          <Card>
            <CardContent className="pt-6">
              <DataTable
                columns={['Invoice', 'Status', 'Amount due', 'Created']}
                rows={failedInvoices.map((invoice) => [
                  invoice.invoice_number ?? invoice.stripe_invoice_id.slice(0, 14),
                  invoice.status,
                  formatPrice(invoice.amount_due_cents, invoice.currency),
                  new Date(invoice.created_at).toLocaleDateString(),
                ])}
                emptyMessage="No failed invoices"
              />
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  );
}
