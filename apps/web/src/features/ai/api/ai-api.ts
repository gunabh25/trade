import type {
  AIChatRequest,
  AICompletion,
  AIConversation,
  AIFeatureType,
  AIPromptRequest,
  AIStatus,
  AIStreamEvent,
} from '@tradeflow/types/api';

import { apiRequest, buildApiUrl } from '@/lib/api/client';

function normalizeCompletion(raw: Record<string, unknown>): AICompletion {
  return {
    content: typeof raw.content === 'string' ? raw.content : '',
    model: typeof raw.model === 'string' ? raw.model : '',
    provider: typeof raw.provider === 'string' ? raw.provider : '',
    finish_reason: typeof raw.finish_reason === 'string' ? raw.finish_reason : null,
    prompt_tokens: typeof raw.prompt_tokens === 'number' ? raw.prompt_tokens : null,
    completion_tokens: typeof raw.completion_tokens === 'number' ? raw.completion_tokens : null,
  };
}

export async function fetchAiStatus(): Promise<AIStatus> {
  const response = await apiRequest<AIStatus>('/ai/status');
  return response.data;
}

export async function sendAiChat(payload: AIChatRequest): Promise<AICompletion> {
  const response = await apiRequest<Record<string, unknown>>('/ai/chat', {
    method: 'POST',
    body: payload,
  });
  return normalizeCompletion(response.data);
}

export async function runAiPrompt(
  endpoint: string,
  payload: AIPromptRequest = {},
): Promise<AICompletion> {
  const response = await apiRequest<Record<string, unknown>>(endpoint, {
    method: 'POST',
    body: payload,
  });
  return normalizeCompletion(response.data);
}

export async function listAiConversations(feature?: AIFeatureType): Promise<AIConversation[]> {
  const query = feature ? `?feature=${feature}` : '';
  const response = await apiRequest<AIConversation[]>(`/ai/conversations${query}`);
  return response.data;
}

export async function streamAiChat(
  payload: AIChatRequest,
  onEvent: (event: AIStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const url = buildApiUrl('/ai/chat/stream');
  const csrfMatch = /(?:^|; )tf_csrf=([^;]*)/.exec(document.cookie);
  const csrf = csrfMatch?.[1] ? decodeURIComponent(csrfMatch[1]) : undefined;

  const init: RequestInit = {
    method: 'POST',
    headers: {
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
      ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
    },
    credentials: 'include',
    body: JSON.stringify(payload),
  };
  if (signal) {
    init.signal = signal;
  }

  const response = await fetch(url, init);

  if (!response.ok || !response.body) {
    throw new Error(`AI stream failed (${String(response.status)})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  for (;;) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';
    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith('data: ')) continue;
      const event = JSON.parse(line.slice(6)) as AIStreamEvent;
      onEvent(event);
    }
  }
}

export const aiEndpoints = {
  tradeExplain: '/ai/trade/explain',
  tradeSummarize: '/ai/trade/summarize',
  riskAnalyze: '/ai/risk/analyze',
  riskDailySummary: '/ai/risk/daily-summary',
  journalSummarize: '/ai/journal/summarize',
  journalPatterns: '/ai/journal/patterns',
  analyticsReport: '/ai/analytics/report',
  analyticsInsights: '/ai/analytics/insights',
  strategyCompare: '/ai/strategy/compare',
  strategyOptimize: '/ai/strategy/optimize',
} as const;
