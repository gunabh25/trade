import type {
  HealthSummaryResponse,
  LivenessResponse,
  ReadinessResponse,
} from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api/client';
import { toNumber, toString } from '@/lib/api/normalize';

export async function fetchLiveness(): Promise<LivenessResponse> {
  const response = await apiRequest<LivenessResponse>('/health/live');
  return response.data;
}

function mapComponentHealth(raw: Record<string, unknown> | undefined) {
  const health: ReadinessResponse['checks']['database'] = {
    status: toString(raw?.status) as ReadinessResponse['checks']['database']['status'],
  };
  if (raw?.latency_ms != null) {
    health.latencyMs = toNumber(raw.latency_ms);
  }
  if (raw?.message != null) {
    health.message = toString(raw.message);
  }
  return health;
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const response = await apiRequest<Record<string, unknown>>('/health/ready');
  const data = response.data;
  const checks = (data.checks as Record<string, Record<string, unknown>> | undefined) ?? {};

  return {
    status: toString(data.status) as ReadinessResponse['status'],
    service: toString(data.service),
    version: toString(data.version),
    timestamp: toString(data.timestamp),
    checks: {
      database: mapComponentHealth(checks.database),
      redis: mapComponentHealth(checks.redis),
    },
  };
}

export async function fetchHealthSummary(): Promise<HealthSummaryResponse> {
  const response = await apiRequest<Record<string, unknown>>('/health');
  const data = response.data;
  return {
    status: toString(data.status) as HealthSummaryResponse['status'],
    service: toString(data.service),
    version: toString(data.version),
    environment: toString(data.environment),
    timestamp: toString(data.timestamp),
  };
}
