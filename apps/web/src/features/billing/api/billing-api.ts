import type {
  BillingOverview,
  CheckoutRequest,
  CouponInfo,
  Invoice,
  Plan,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import { toNullableString, toNumber, toString } from '@/lib/api/normalize';

function normalizePlan(raw: Record<string, unknown>): Plan {
  return {
    id: toString(raw.id),
    code: toString(raw.code),
    name: toString(raw.name),
    description: toNullableString(raw.description),
    price_cents: toNumber(raw.price_cents),
    currency: toString(raw.currency),
    interval: toString(raw.interval) as Plan['interval'],
    max_trading_accounts: toNumber(raw.max_trading_accounts),
    max_broker_connections: toNumber(raw.max_broker_connections),
    max_copy_groups: toNumber(raw.max_copy_groups),
    trial_days: toNumber(raw.trial_days),
    features: (raw.features as Record<string, unknown> | null) ?? null,
    is_active: Boolean(raw.is_active),
  };
}

function normalizeOverview(raw: Record<string, unknown>): BillingOverview {
  const subscription = raw.subscription as Record<string, unknown>;
  const planRaw = subscription.plan as Record<string, unknown>;
  const usageRaw = Array.isArray(raw.usage) ? raw.usage : [];

  return {
    subscription: {
      id: toString(subscription.id),
      status: toString(subscription.status) as BillingOverview['subscription']['status'],
      plan: normalizePlan(planRaw),
      trial_ends_at: toNullableString(subscription.trial_ends_at),
      current_period_start: toNullableString(subscription.current_period_start),
      current_period_end: toNullableString(subscription.current_period_end),
      canceled_at: toNullableString(subscription.canceled_at),
      coupon_code: toNullableString(subscription.coupon_code),
      is_trialing: Boolean(subscription.is_trialing),
      cancel_at_period_end: Boolean(subscription.cancel_at_period_end),
      payment_action_required: Boolean(subscription.payment_action_required),
    },
    usage: usageRaw.map((item) => {
      const row = item as Record<string, unknown>;
      return {
        metric: toString(row.metric) as BillingOverview['usage'][number]['metric'],
        used: toNumber(row.used),
        limit: toNumber(row.limit),
        percent: toNumber(row.percent),
      };
    }),
    stripe_enabled: Boolean(raw.stripe_enabled),
    publishable_key: toNullableString(raw.publishable_key),
  };
}

function normalizeInvoice(raw: Record<string, unknown>): Invoice {
  return {
    id: toString(raw.id),
    stripe_invoice_id: toString(raw.stripe_invoice_id),
    invoice_number: toNullableString(raw.invoice_number),
    status: toString(raw.status) as Invoice['status'],
    amount_due_cents: toNumber(raw.amount_due_cents),
    amount_paid_cents: toNumber(raw.amount_paid_cents),
    currency: toString(raw.currency),
    hosted_invoice_url: toNullableString(raw.hosted_invoice_url),
    invoice_pdf_url: toNullableString(raw.invoice_pdf_url),
    period_start: toNullableString(raw.period_start),
    period_end: toNullableString(raw.period_end),
    paid_at: toNullableString(raw.paid_at),
    created_at: toString(raw.created_at),
  };
}

export async function listPlans(): Promise<Plan[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/billing/plans');
  return response.data.map((item) => normalizePlan(item));
}

export async function getBillingOverview(): Promise<BillingOverview> {
  const response = await apiRequest<Record<string, unknown>>('/billing/overview');
  return normalizeOverview(response.data);
}

export async function createCheckout(body: CheckoutRequest): Promise<string> {
  const response = await apiRequest<{ checkout_url: string }>('/billing/checkout', {
    method: 'POST',
    body,
  });
  return response.data.checkout_url;
}

export async function createPortalSession(): Promise<string> {
  const response = await apiRequest<{ portal_url: string }>('/billing/portal', {
    method: 'POST',
  });
  return response.data.portal_url;
}

export async function validateCoupon(code: string, planCode?: string): Promise<CouponInfo> {
  const response = await apiRequest<Record<string, unknown>>('/billing/coupons/validate', {
    method: 'POST',
    body: { code, plan_code: planCode ?? null },
  });
  const raw = response.data;
  return {
    id: toString(raw.id),
    code: toString(raw.code),
    name: toString(raw.name),
    discount_type: toString(raw.discount_type) as CouponInfo['discount_type'],
    percent_off: raw.percent_off != null ? toNumber(raw.percent_off) : null,
    amount_off_cents: raw.amount_off_cents != null ? toNumber(raw.amount_off_cents) : null,
    currency: toNullableString(raw.currency),
    duration: toString(raw.duration) as CouponInfo['duration'],
    active: Boolean(raw.active),
    expires_at: toNullableString(raw.expires_at),
  };
}

export async function listInvoices(): Promise<Invoice[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/billing/invoices');
  return response.data.map((item) => normalizeInvoice(item));
}

export async function changeSubscriptionPlan(planCode: string): Promise<void> {
  await apiRequest('/billing/subscription/change', {
    method: 'POST',
    body: { plan_code: planCode },
  });
}

export async function cancelSubscription(atPeriodEnd = true): Promise<void> {
  await apiRequest('/billing/subscription/cancel', {
    method: 'POST',
    body: { at_period_end: atPeriodEnd },
  });
}

export function formatPrice(cents: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
  }).format(cents / 100);
}
