export type AIFeatureType =
  | 'trade_assistant'
  | 'risk_advisor'
  | 'journal'
  | 'analytics'
  | 'strategy';

export interface AICompletion {
  content: string;
  model: string;
  provider: string;
  finish_reason?: string | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
}

export interface AIChatRequest {
  message: string;
  feature?: AIFeatureType;
  conversation_id?: string;
  provider?: string;
  model?: string;
}

export interface AIPromptRequest {
  question?: string;
  period?: 'weekly' | 'monthly';
  conversation_id?: string;
  provider?: string;
  model?: string;
  use_tools?: boolean;
}

export interface AIMessage {
  id: string;
  role: string;
  content: string;
  token_count?: number | null;
  created_at: string;
}

export interface AIConversation {
  id: string;
  feature_type: string;
  title?: string | null;
  provider: string;
  model: string;
  created_at: string;
  updated_at: string;
  messages?: AIMessage[];
}

export interface AIStatus {
  enabled: boolean;
  configured: boolean;
  default_provider: string;
  providers: string[];
}

export interface AIStreamEvent {
  type: 'token' | 'done' | 'error';
  content?: string;
  error?: string;
  metadata?: Record<string, string>;
}
