export interface RiskRule {
  id: string;
  trading_account_id: string;
  name: string;
  enabled: boolean;
  kill_switch_active: boolean;
  daily_loss_limit_usd: number | null;
  trailing_drawdown_limit_usd: number | null;
  max_position_size_usd: number | null;
  max_contracts_per_symbol: number | null;
  max_total_contracts: number | null;
  max_leverage: number | null;
  allowed_symbols: string[] | null;
  blocked_symbols: string[] | null;
  trading_hours_start: string | null;
  trading_hours_end: string | null;
  trading_hours_timezone: string | null;
  session_reset_time: string | null;
  auto_flatten_on_breach: boolean;
  auto_stop_copying_on_breach: boolean;
  created_at: string;
}

export interface RiskBreach {
  id: string;
  trading_account_id: string;
  breach_type: string;
  action_taken: string;
  message: string;
  current_value: number | null;
  limit_value: number | null;
  symbol: string | null;
  created_at: string;
}

export interface RiskMonitorStatus {
  trading_account_id: string;
  status: string;
  daily_pnl: number | null;
  drawdown_usd: number | null;
  peak_equity: number | null;
  current_equity: number | null;
  total_open_contracts: number | null;
  current_leverage: number | null;
  kill_switch_active: boolean;
  checked_at: string;
}

export interface RiskRuleConfig {
  name?: string;
  enabled?: boolean;
  daily_loss_limit_usd?: number | null;
  trailing_drawdown_limit_usd?: number | null;
  max_position_size_usd?: number | null;
  max_contracts_per_symbol?: number | null;
  max_total_contracts?: number | null;
  max_leverage?: number | null;
  allowed_symbols?: string[] | null;
  blocked_symbols?: string[] | null;
  trading_hours_start?: string | null;
  trading_hours_end?: string | null;
  trading_hours_timezone?: string;
  session_reset_time?: string | null;
  auto_flatten_on_breach?: boolean;
  auto_stop_copying_on_breach?: boolean;
}

export interface CreateRiskRuleRequest extends RiskRuleConfig {
  trading_account_id: string;
}

export interface PreTradeCheckRequest {
  symbol: string;
  side: string;
  quantity: number;
}
