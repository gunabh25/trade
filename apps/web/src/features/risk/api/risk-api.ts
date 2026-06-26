import type {
  CreateRiskRuleRequest,
  PreTradeCheckRequest,
  RiskBreach,
  RiskMonitorStatus,
  RiskRule,
  RiskRuleConfig,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import {
  toNullableNumber,
  toNullableString,
  toNumber,
  toString,
  toStringArray,
} from '@/lib/api/normalize';

function normalizeRule(raw: Record<string, unknown>): RiskRule {
  return {
    id: toString(raw.id),
    trading_account_id: toString(raw.trading_account_id),
    name: toString(raw.name),
    enabled: Boolean(raw.enabled),
    kill_switch_active: Boolean(raw.kill_switch_active),
    daily_loss_limit_usd: toNullableNumber(raw.daily_loss_limit_usd),
    trailing_drawdown_limit_usd: toNullableNumber(raw.trailing_drawdown_limit_usd),
    max_position_size_usd: toNullableNumber(raw.max_position_size_usd),
    max_contracts_per_symbol:
      raw.max_contracts_per_symbol != null ? toNumber(raw.max_contracts_per_symbol) : null,
    max_total_contracts: raw.max_total_contracts != null ? toNumber(raw.max_total_contracts) : null,
    max_leverage: toNullableNumber(raw.max_leverage),
    allowed_symbols: toStringArray(raw.allowed_symbols),
    blocked_symbols: toStringArray(raw.blocked_symbols),
    trading_hours_start: toNullableString(raw.trading_hours_start),
    trading_hours_end: toNullableString(raw.trading_hours_end),
    trading_hours_timezone: toNullableString(raw.trading_hours_timezone),
    session_reset_time: toNullableString(raw.session_reset_time),
    auto_flatten_on_breach: Boolean(raw.auto_flatten_on_breach),
    auto_stop_copying_on_breach: Boolean(raw.auto_stop_copying_on_breach),
    created_at: toString(raw.created_at),
  };
}

function normalizeBreach(raw: Record<string, unknown>): RiskBreach {
  return {
    id: toString(raw.id),
    trading_account_id: toString(raw.trading_account_id),
    breach_type: toString(raw.breach_type),
    action_taken: toString(raw.action_taken),
    message: toString(raw.message),
    current_value: toNullableNumber(raw.current_value),
    limit_value: toNullableNumber(raw.limit_value),
    symbol: toNullableString(raw.symbol),
    created_at: toString(raw.created_at),
  };
}

function normalizeMonitorStatus(raw: Record<string, unknown>): RiskMonitorStatus {
  return {
    trading_account_id: toString(raw.trading_account_id),
    status: toString(raw.status),
    daily_pnl: toNullableNumber(raw.daily_pnl),
    drawdown_usd: toNullableNumber(raw.drawdown_usd),
    peak_equity: toNullableNumber(raw.peak_equity),
    current_equity: toNullableNumber(raw.current_equity),
    total_open_contracts:
      raw.total_open_contracts != null ? toNumber(raw.total_open_contracts) : null,
    current_leverage: toNullableNumber(raw.current_leverage),
    kill_switch_active: Boolean(raw.kill_switch_active),
    checked_at: toString(raw.checked_at),
  };
}

export async function listRiskRules(): Promise<RiskRule[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/risk/rules');
  return response.data.map((item) => normalizeRule(item));
}

export async function getRiskRule(ruleId: string): Promise<RiskRule> {
  const response = await apiRequest<Record<string, unknown>>(`/risk/rules/${ruleId}`);
  return normalizeRule(response.data);
}

export async function createRiskRule(payload: CreateRiskRuleRequest): Promise<RiskRule> {
  const response = await apiRequest<Record<string, unknown>>('/risk/rules', {
    method: 'POST',
    body: payload,
  });
  return normalizeRule(response.data);
}

export async function updateRiskRule(ruleId: string, payload: RiskRuleConfig): Promise<RiskRule> {
  const response = await apiRequest<Record<string, unknown>>(`/risk/rules/${ruleId}`, {
    method: 'PUT',
    body: payload,
  });
  return normalizeRule(response.data);
}

export async function deleteRiskRule(ruleId: string): Promise<void> {
  await apiRequest<{ status: string }>(`/risk/rules/${ruleId}`, { method: 'DELETE' });
}

export async function activateKillSwitch(ruleId: string): Promise<RiskRule> {
  const response = await apiRequest<Record<string, unknown>>(
    `/risk/rules/${ruleId}/kill-switch/activate`,
    { method: 'POST' },
  );
  return normalizeRule(response.data);
}

export async function deactivateKillSwitch(ruleId: string): Promise<RiskRule> {
  const response = await apiRequest<Record<string, unknown>>(
    `/risk/rules/${ruleId}/kill-switch/deactivate`,
    { method: 'POST' },
  );
  return normalizeRule(response.data);
}

export async function flattenAccount(accountId: string): Promise<{ flattened: number }> {
  const response = await apiRequest<Record<string, unknown>>(
    `/risk/accounts/${accountId}/flatten`,
    { method: 'POST' },
  );
  return { flattened: toNumber(response.data.flattened) };
}

export async function getAccountRiskStatus(accountId: string): Promise<RiskMonitorStatus> {
  const response = await apiRequest<Record<string, unknown>>(`/risk/accounts/${accountId}/status`);
  return normalizeMonitorStatus(response.data);
}

export async function listRiskBreaches(accountId?: string): Promise<RiskBreach[]> {
  const qs = accountId ? `?account_id=${accountId}` : '';
  const response = await apiRequest<Record<string, unknown>[]>(`/risk/breaches${qs}`);
  return response.data.map((item) => normalizeBreach(item));
}

export async function preTradeRiskCheck(
  accountId: string,
  payload: PreTradeCheckRequest,
): Promise<Record<string, unknown>> {
  const params = new URLSearchParams({
    symbol: payload.symbol,
    side: payload.side,
    quantity: String(payload.quantity),
  });
  const response = await apiRequest<Record<string, unknown>>(
    `/risk/accounts/${accountId}/check?${params.toString()}`,
    { method: 'POST' },
  );
  return response.data;
}
