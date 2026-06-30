'use client';

import { Bot, Loader2, Send, Sparkles } from 'lucide-react';
import { useState } from 'react';

import type { AIFeatureType } from '@tradeflow/types/api';
import { Button, Card, CardContent, CardHeader, CardTitle, cn } from '@tradeflow/ui';

import { aiEndpoints } from '@/features/ai/api/ai-api';
import { useAiChat } from '@/features/ai/hooks/use-ai-chat';

const FEATURES: { id: AIFeatureType; label: string; prompt: string; endpoint?: string }[] = [
  {
    id: 'trade_assistant',
    label: 'Trade Assistant',
    prompt: 'Summarize my recent trading activity',
  },
  {
    id: 'risk_advisor',
    label: 'Risk Advisor',
    prompt: 'Analyze my risk exposure',
    endpoint: aiEndpoints.riskAnalyze,
  },
  {
    id: 'journal',
    label: 'Journal Coach',
    prompt: 'Find emotional patterns in my journal',
    endpoint: aiEndpoints.journalPatterns,
  },
  {
    id: 'analytics',
    label: 'Analytics',
    prompt: 'Weekly performance report',
    endpoint: aiEndpoints.analyticsReport,
  },
  {
    id: 'strategy',
    label: 'Strategy',
    prompt: 'Compare my strategies',
    endpoint: aiEndpoints.strategyCompare,
  },
];

export function AiAssistantPanel() {
  const [feature, setFeature] = useState<AIFeatureType>('trade_assistant');
  const [input, setInput] = useState('');
  const { messages, loading, streaming, error, send, runPrompt } = useAiChat(feature);

  const active = FEATURES.find((f) => f.id === feature) ??
    FEATURES[0] ?? {
      id: 'trade_assistant' as AIFeatureType,
      label: 'Trade Assistant',
      prompt: 'Summarize my recent trading activity',
    };

  async function handleQuickAction() {
    if (active.endpoint) {
      await runPrompt(active.endpoint, active.prompt);
    } else {
      await send(active.prompt, { feature, stream: true });
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
      <Card className="border-border/60 bg-card/80 h-fit">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="text-primary h-4 w-4" />
            AI Modules
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {FEATURES.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setFeature(item.id);
              }}
              className={cn(
                'w-full rounded-lg px-3 py-2 text-left text-sm transition-colors',
                feature === item.id
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground',
              )}
            >
              {item.label}
            </button>
          ))}
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/80 flex min-h-[560px] flex-col">
        <CardHeader className="border-border/60 border-b">
          <CardTitle className="flex items-center gap-2 text-base">
            <Bot className="h-4 w-4" />
            {active.label}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col gap-4 p-4">
          <div className="flex-1 space-y-3 overflow-y-auto pr-1">
            {messages.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                Ask about trades, PnL, risk, journal patterns, analytics, or strategy optimization.
              </p>
            ) : (
              messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    'max-w-[90%] rounded-xl px-4 py-3 text-sm',
                    msg.role === 'user'
                      ? 'bg-primary/15 text-foreground ml-auto'
                      : 'bg-muted/40 text-foreground',
                  )}
                >
                  {msg.content}
                </div>
              ))
            )}
            {(loading || streaming) && (
              <div className="text-muted-foreground flex items-center gap-2 text-sm">
                <Loader2 className="h-4 w-4 animate-spin" />
                {streaming ? 'Streaming response…' : 'Thinking…'}
              </div>
            )}
            {error ? <p className="text-destructive text-sm">{error}</p> : null}
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => void handleQuickAction()}
              disabled={loading}
            >
              Quick: {active.label}
            </Button>
          </div>

          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!input.trim() || loading) return;
              void send(input.trim(), { feature, stream: true });
              setInput('');
            }}
          >
            <input
              className="border-input bg-background flex-1 rounded-lg border px-3 py-2 text-sm"
              placeholder="Ask TradeFlow AI…"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
              }}
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
