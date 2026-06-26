export type BrokerConnectionStatus = 'pending' | 'connected' | 'disconnected' | 'error';

export interface BrokerConnection {
  id: string;
  broker: string;
  name: string;
  status: BrokerConnectionStatus;
  last_connected_at: string | null;
  last_error: string | null;
  created_at: string;
}

export interface BrokerHealth {
  connection_id: string;
  status: string;
  connected: boolean;
  websocket_connected: boolean;
  latency_ms: number | null;
  reconnect_attempts: number;
  last_error: string | null;
}

export interface BrokerAccount {
  id: string;
  name: string;
  currency: string;
  balance: number;
  equity: number;
  is_live: boolean;
}

export interface BrokerOrder {
  id: string;
  account_id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: number;
  price: number | null;
  status: string;
  filled_quantity: number;
}

export interface BrokerPosition {
  id: string;
  account_id: string;
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
}

export interface CreateBrokerConnectionRequest {
  broker: string;
  name: string;
  credentials: Record<string, unknown>;
}

export interface PlaceBrokerOrderRequest {
  account_id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: number;
  price?: number | null;
}

export interface SupportedBrokers {
  brokers: string[];
}
