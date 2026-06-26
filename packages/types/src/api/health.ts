export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface ComponentHealth {
  status: HealthStatus;
  latencyMs?: number;
  message?: string;
}

export interface LivenessResponse {
  status: 'alive';
  service: string;
  version: string;
  timestamp: string;
}

export interface ReadinessResponse {
  status: HealthStatus;
  service: string;
  version: string;
  timestamp: string;
  checks: {
    database: ComponentHealth;
    redis: ComponentHealth;
  };
}

export interface HealthSummaryResponse {
  status: HealthStatus;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}
