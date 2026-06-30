import { AiAssistantPanel } from '@/features/ai/components/ai-assistant-panel';

export default function AiPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">AI Assistant</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Trade assistant, risk advisor, journal coach, analytics, and strategy insights.
        </p>
      </div>
      <AiAssistantPanel />
    </div>
  );
}
