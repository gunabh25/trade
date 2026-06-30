'use client';

import { useCallback, useState } from 'react';

import type { AICompletion, AIFeatureType, AIStreamEvent } from '@tradeflow/types/api';

import * as aiApi from '@/features/ai/api/ai-api';

export function useAiChat(initialFeature: AIFeatureType = 'trade_assistant') {
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(
    async (message: string, options?: { stream?: boolean; feature?: AIFeatureType }) => {
      setError(null);
      setLoading(true);
      setMessages((prev) => [...prev, { role: 'user', content: message }]);

      try {
        if (options?.stream) {
          setStreaming(true);
          let assistant = '';
          setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);
          await aiApi.streamAiChat(
            { message, feature: options.feature ?? initialFeature },
            (event: AIStreamEvent) => {
              if (event.type === 'token' && event.content) {
                assistant += event.content;
                setMessages((prev) => {
                  const next = [...prev];
                  next[next.length - 1] = { role: 'assistant', content: assistant };
                  return next;
                });
              }
              if (event.type === 'error') {
                setError(event.error ?? 'Stream failed');
              }
            },
          );
        } else {
          const result: AICompletion = await aiApi.sendAiChat({
            message,
            feature: options?.feature ?? initialFeature,
          });
          setMessages((prev) => [...prev, { role: 'assistant', content: result.content }]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'AI request failed');
      } finally {
        setLoading(false);
        setStreaming(false);
      }
    },
    [initialFeature],
  );

  const runPrompt = useCallback(async (endpoint: string, question?: string) => {
    setError(null);
    setLoading(true);
    try {
      const result = await aiApi.runAiPrompt(endpoint, question ? { question } : {});
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: question ?? 'Generate analysis' },
        { role: 'assistant', content: result.content },
      ]);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI request failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { messages, loading, streaming, error, send, runPrompt };
}
