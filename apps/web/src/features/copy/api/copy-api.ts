import type {
  AddCopyFollowerRequest,
  CopyEngineHealth,
  CopyEvent,
  CopyGroup,
  CopyGroupFollower,
  CreateCopyGroupRequest,
  ExecutionLog,
  SimulateLeaderEventRequest,
  UpdateCopyGroupRequest,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import { toNullableString, toNumber, toString } from '@/lib/api/normalize';

function normalizeFollower(raw: Record<string, unknown>): CopyGroupFollower {
  return {
    id: toString(raw.id),
    follower_account_id: toString(raw.follower_account_id),
    enabled: Boolean(raw.enabled),
    copy_mode: toString(raw.copy_mode),
    sizing_value: toNumber(raw.sizing_value),
    status: toString(raw.status),
  };
}

function normalizeGroup(raw: Record<string, unknown>): CopyGroup {
  return {
    id: toString(raw.id),
    name: toString(raw.name),
    leader_account_id: toString(raw.leader_account_id),
    mode: toString(raw.mode),
    status: toString(raw.status),
    copying_enabled: Boolean(raw.copying_enabled),
    sim_validated: Boolean(raw.sim_validated),
    followers: Array.isArray(raw.followers)
      ? raw.followers.map((item) => normalizeFollower(item as Record<string, unknown>))
      : [],
    created_at: toString(raw.created_at),
  };
}

function normalizeEvent(raw: Record<string, unknown>): CopyEvent {
  return {
    id: toString(raw.id),
    copy_group_id: toString(raw.copy_group_id),
    leader_account_id: toString(raw.leader_account_id),
    follower_account_id: toNullableString(raw.follower_account_id),
    leader_event_id: toString(raw.leader_event_id),
    action: toString(raw.action),
    result: toString(raw.result),
    symbol: toNullableString(raw.symbol),
    quantity: raw.quantity != null ? toNumber(raw.quantity) : null,
    latency_ms: raw.latency_ms != null ? toNumber(raw.latency_ms) : null,
    error_message: toNullableString(raw.error_message),
    created_at: toString(raw.created_at),
  };
}

function normalizeExecutionLog(raw: Record<string, unknown>): ExecutionLog {
  return {
    id: toString(raw.id),
    copy_group_id: toString(raw.copy_group_id),
    follower_account_id: toString(raw.follower_account_id),
    action: toString(raw.action),
    status: toString(raw.status),
    attempt: toNumber(raw.attempt),
    max_attempts: toNumber(raw.max_attempts),
    error_message: toNullableString(raw.error_message),
    latency_ms: raw.latency_ms != null ? toNumber(raw.latency_ms) : null,
    created_at: toString(raw.created_at),
  };
}

export async function listCopyGroups(): Promise<CopyGroup[]> {
  const response = await apiRequest<Record<string, unknown>[]>('/copy/groups');
  return response.data.map((item) => normalizeGroup(item));
}

export async function getCopyGroup(groupId: string): Promise<CopyGroup> {
  const response = await apiRequest<Record<string, unknown>>(`/copy/groups/${groupId}`);
  return normalizeGroup(response.data);
}

export async function createCopyGroup(payload: CreateCopyGroupRequest): Promise<CopyGroup> {
  const response = await apiRequest<Record<string, unknown>>('/copy/groups', {
    method: 'POST',
    body: payload,
    timeoutMs: 30_000,
  });
  return normalizeGroup(response.data);
}

export async function updateCopyGroup(
  groupId: string,
  payload: UpdateCopyGroupRequest,
): Promise<CopyGroup> {
  const response = await apiRequest<Record<string, unknown>>(`/copy/groups/${groupId}`, {
    method: 'PUT',
    body: payload,
    timeoutMs: 30_000,
  });
  return normalizeGroup(response.data);
}

export async function addCopyFollower(
  groupId: string,
  payload: AddCopyFollowerRequest,
): Promise<CopyGroupFollower> {
  const response = await apiRequest<Record<string, unknown>>(`/copy/groups/${groupId}/followers`, {
    method: 'POST',
    body: payload,
    timeoutMs: 30_000,
  });
  return normalizeFollower(response.data);
}

export async function startCopyGroup(groupId: string): Promise<CopyGroup> {
  const response = await apiRequest<Record<string, unknown>>(`/copy/groups/${groupId}/start`, {
    method: 'POST',
    timeoutMs: 30_000,
  });
  return normalizeGroup(response.data);
}

export async function stopCopyGroup(groupId: string): Promise<CopyGroup> {
  const response = await apiRequest<Record<string, unknown>>(`/copy/groups/${groupId}/stop`, {
    method: 'POST',
  });
  return normalizeGroup(response.data);
}

export async function deleteCopyGroup(groupId: string): Promise<void> {
  await apiRequest<Record<string, unknown>>(`/copy/groups/${groupId}`, {
    method: 'DELETE',
  });
}

export async function listCopyEvents(groupId: string): Promise<CopyEvent[]> {
  const response = await apiRequest<Record<string, unknown>[]>(`/copy/groups/${groupId}/events`);
  return response.data.map((item) => normalizeEvent(item));
}

export async function listExecutionLogs(groupId: string): Promise<ExecutionLog[]> {
  const response = await apiRequest<Record<string, unknown>[]>(
    `/copy/groups/${groupId}/execution-logs`,
  );
  return response.data.map((item) => normalizeExecutionLog(item));
}

export async function simulateCopyEvent(
  groupId: string,
  payload: SimulateLeaderEventRequest,
): Promise<Record<string, unknown>[]> {
  const response = await apiRequest<Record<string, unknown>[]>(`/copy/groups/${groupId}/simulate`, {
    method: 'POST',
    body: payload,
  });
  return response.data;
}

export async function getCopyEngineHealth(): Promise<CopyEngineHealth> {
  const response = await apiRequest<Record<string, unknown>>('/copy/health');
  return {
    active_groups: toNumber(response.data.active_groups),
    retry_queue_depth: toNumber(response.data.retry_queue_depth),
    dead_letter_count: toNumber(response.data.dead_letter_count),
  };
}
