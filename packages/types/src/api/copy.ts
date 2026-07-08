export interface CopyGroupFollower {
  id: string;
  follower_account_id: string;
  enabled: boolean;
  copy_mode: string;
  sizing_value: number;
  status: string;
}

export interface CopyGroup {
  id: string;
  name: string;
  leader_account_id: string;
  mode: string;
  status: string;
  copying_enabled: boolean;
  sim_validated: boolean;
  followers: CopyGroupFollower[];
  created_at: string;
}

export interface CopyEvent {
  id: string;
  copy_group_id: string;
  leader_account_id: string;
  follower_account_id: string | null;
  leader_event_id: string;
  action: string;
  result: string;
  symbol: string | null;
  quantity: number | null;
  latency_ms: number | null;
  error_message: string | null;
  created_at: string;
}

export interface ExecutionLog {
  id: string;
  copy_group_id: string;
  follower_account_id: string;
  action: string;
  status: string;
  attempt: number;
  max_attempts: number;
  error_message: string | null;
  latency_ms: number | null;
  created_at: string;
}

export interface CopyEngineHealth {
  active_groups: number;
  retry_queue_depth: number;
  dead_letter_count: number;
}

export interface CreateCopyGroupRequest {
  name: string;
  leader_account_id: string;
  mode?: string;
}

export interface UpdateCopyGroupRequest {
  name: string;
  leader_account_id: string;
  mode?: string;
}

export interface AddCopyFollowerRequest {
  follower_account_id: string;
  copy_mode: string;
  sizing_value: number;
}

export interface SimulateLeaderEventRequest {
  symbol: string;
  side: 'buy' | 'sell';
  order_type?: string;
  quantity: number;
  price?: number | null;
  stop_price?: number | null;
  leader_order_id?: string | null;
}
