export type PlanInterval = 'month' | 'year';

export type SubscriptionStatus = 'trialing' | 'active' | 'past_due' | 'canceled' | 'incomplete';

export type InvoiceStatus = 'draft' | 'open' | 'paid' | 'void' | 'uncollectible';

export type BillingEventType =
  | 'invoice_paid'
  | 'invoice_failed'
  | 'subscription_created'
  | 'subscription_updated'
  | 'subscription_canceled'
  | 'refund'
  | 'trial_started'
  | 'trial_ended'
  | 'coupon_applied';

export type UsageMetric =
  | 'trading_accounts'
  | 'broker_connections'
  | 'copy_groups'
  | 'api_requests';

export interface Plan {
  id: string;
  code: string;
  name: string;
  description: string | null;
  price_cents: number;
  currency: string;
  interval: PlanInterval;
  max_trading_accounts: number;
  max_broker_connections: number;
  max_copy_groups: number;
  trial_days: number;
  features: Record<string, unknown> | null;
  is_active: boolean;
  stripe_price_id?: string | null;
}

export interface UsageItem {
  metric: UsageMetric;
  used: number;
  limit: number;
  percent: number;
}

export interface Subscription {
  id: string;
  status: SubscriptionStatus;
  plan: Plan;
  trial_ends_at: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  canceled_at: string | null;
  coupon_code: string | null;
  is_trialing: boolean;
  cancel_at_period_end?: boolean;
  payment_action_required?: boolean;
}

export interface BillingOverview {
  subscription: Subscription;
  usage: UsageItem[];
  stripe_enabled: boolean;
  publishable_key: string | null;
}

export interface Invoice {
  id: string;
  stripe_invoice_id: string;
  invoice_number: string | null;
  status: InvoiceStatus;
  amount_due_cents: number;
  amount_paid_cents: number;
  currency: string;
  hosted_invoice_url: string | null;
  invoice_pdf_url: string | null;
  period_start: string | null;
  period_end: string | null;
  paid_at: string | null;
  created_at: string;
}

export interface BillingEvent {
  id: string;
  event_type: BillingEventType;
  status: 'pending' | 'succeeded' | 'failed';
  amount_cents: number | null;
  currency: string | null;
  stripe_invoice_id: string | null;
  created_at: string;
}

export interface CheckoutRequest {
  plan_code: string;
  coupon_code?: string | null;
}

export interface ChangePlanRequest {
  plan_code: string;
}

export interface CancelSubscriptionRequest {
  at_period_end?: boolean;
}

export interface CouponInfo {
  id: string;
  code: string;
  name: string;
  discount_type: 'percent' | 'amount';
  percent_off: number | null;
  amount_off_cents: number | null;
  currency: string | null;
  duration: 'once' | 'repeating' | 'forever';
  active: boolean;
  times_redeemed?: number;
  max_redemptions?: number | null;
  expires_at: string | null;
}

export interface AdminCreateCouponRequest {
  code: string;
  name: string;
  discount_type: 'percent' | 'amount';
  percent_off?: number;
  amount_off_cents?: number;
  duration?: 'once' | 'repeating' | 'forever';
  duration_in_months?: number;
  max_redemptions?: number;
  expires_at?: string;
  applicable_plan_codes?: string[];
}

export interface AdminUpdatePlanRequest {
  stripe_price_id?: string;
  stripe_product_id?: string;
  price_cents?: number;
  trial_days?: number;
  is_active?: boolean;
  features?: Record<string, unknown>;
}
