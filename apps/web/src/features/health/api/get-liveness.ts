import type { LivenessResponse } from '@tradeflow/types/api';

import { apiRequest } from '@/lib/api';

export async function fetchLiveness(): Promise<LivenessResponse> {
  const response = await apiRequest<LivenessResponse>('/health/live');
  return response.data;
}
