import type {
  BrokerAccount,
  BrokerConnection,
  BrokerHealth,
  BrokerOrder,
  BrokerPosition,
  CreateBrokerConnectionRequest,
  PlaceBrokerOrderRequest,
  SupportedBrokers,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import { toNullableNumber, toNullableString, toNumber, toString } from '@/lib/api/normalize';

function normalizeConnection(raw: Record<string, unknown>): BrokerConnection {
  return {
    id: toString(raw.id),
    broker: toString(raw.broker),
    name: toString(raw.name),
    status: toString(raw.status) as BrokerConnection['status'],
    last_connected_at: toNullableString(raw.last_connected_at),
    last_error: toNullableString(raw.last_error),
    created_at: toString(raw.created_at),
  };
}

function normalizeAccount(raw: Record<string, unknown>): BrokerAccount {
  return {
    id: toString(raw.id),
    name: toString(raw.name),
    currency: toString(raw.currency),
    balance: toNumber(raw.balance),
    equity: toNumber(raw.equity),
    is_live: Boolean(raw.is_live),
  };
}

function normalizeOrder(raw: Record<string, unknown>): BrokerOrder {
  return {
    id: toString(raw.id),
    account_id: toString(raw.account_id),
    symbol: toString(raw.symbol),
    side: toString(raw.side),
    order_type: toString(raw.order_type),
    quantity: toNumber(raw.quantity),
    price: toNullableNumber(raw.price),
    status: toString(raw.status),
    filled_quantity: toNumber(raw.filled_quantity),
  };
}

function normalizePosition(raw: Record<string, unknown>): BrokerPosition {
  return {
    id: toString(raw.id),
    account_id: toString(raw.account_id),
    symbol: toString(raw.symbol),
    side: toString(raw.side),
    quantity: toNumber(raw.quantity),
    entry_price: toNumber(raw.entry_price),
    mark_price: toNumber(raw.mark_price),
    unrealized_pnl: toNumber(raw.unrealized_pnl),
  };
}

function normalizeHealth(raw: Record<string, unknown>): BrokerHealth {
  return {
    connection_id: toString(raw.connection_id),
    status: toString(raw.status),
    connected: Boolean(raw.connected),
    websocket_connected: Boolean(raw.websocket_connected),
    latency_ms: toNullableNumber(raw.latency_ms),
    reconnect_attempts: toNumber(raw.reconnect_attempts),
    last_error: toNullableString(raw.last_error),
  };
}

export async function listSupportedBrokers(): Promise<SupportedBrokers> {
  const response = await apiRequest<Record<string, unknown>>('/broker/supported');
  const brokers = Array.isArray(response.data.brokers) ? response.data.brokers : [];
  return { brokers: brokers.map(String) };
}

export async function listBrokerConnections(): Promise<BrokerConnection[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/broker/connections');
  return response.data.map((item) => normalizeConnection(item));
}

export async function createBrokerConnection(
  payload: CreateBrokerConnectionRequest,
): Promise<BrokerConnection> {
  const response = await apiRequest<Record<string, unknown>>('/broker/connections', {
    method: 'POST',
    body: payload,
  });
  return normalizeConnection(response.data);
}

export async function connectBroker(connectionId: string): Promise<BrokerHealth> {
  const response = await apiRequest<Record<string, unknown>>(
    `/broker/connections/${connectionId}/connect`,
    { method: 'POST' },
  );
  return normalizeHealth(response.data);
}

export async function disconnectBroker(connectionId: string): Promise<BrokerConnection> {
  const response = await apiRequest<Record<string, unknown>>(
    `/broker/connections/${connectionId}/disconnect`,
    { method: 'POST' },
  );
  return normalizeConnection(response.data);
}

export async function getBrokerHealth(connectionId: string): Promise<BrokerHealth> {
  const response = await apiRequest<Record<string, unknown>>(
    `/broker/connections/${connectionId}/health`,
  );
  return normalizeHealth(response.data);
}

export async function listBrokerAccounts(connectionId: string): Promise<BrokerAccount[]> {
  const response = await apiRequest<Record<string, unknown>[]>(
    `/broker/connections/${connectionId}/accounts`,
  );
  return response.data.map((item) => normalizeAccount(item));
}

export async function listBrokerOrders(
  connectionId: string,
  accountId: string,
): Promise<BrokerOrder[]> {
  const response = await apiRequest<Record<string, unknown>[]>(
    `/broker/connections/${connectionId}/accounts/${accountId}/orders`,
  );
  return response.data.map((item) => normalizeOrder(item));
}

export async function listBrokerPositions(
  connectionId: string,
  accountId: string,
): Promise<BrokerPosition[]> {
  const response = await apiRequest<Record<string, unknown>[]>(
    `/broker/connections/${connectionId}/accounts/${accountId}/positions`,
  );
  return response.data.map((item) => normalizePosition(item));
}

export async function placeBrokerOrder(
  connectionId: string,
  payload: PlaceBrokerOrderRequest,
): Promise<BrokerOrder> {
  const response = await apiRequest<Record<string, unknown>>(
    `/broker/connections/${connectionId}/orders`,
    { method: 'POST', body: payload },
  );
  return normalizeOrder(response.data);
}
