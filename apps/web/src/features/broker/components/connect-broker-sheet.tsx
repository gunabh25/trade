'use client';

import { Loader2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { Button, Input, Sheet, SheetContent, SheetHeader, SheetTitle, cn } from '@tradeflow/ui';

import { connectBroker, createBrokerConnection } from '@/features/broker/api/broker-api';
import {
  defaultFieldValues,
  getBrokerFormConfig,
  ONBOARDING_BROKERS,
  type BrokerFormConfig,
} from '@/features/broker/config/broker-forms';
import { ApiClientError } from '@/lib/errors';

interface ConnectBrokerSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConnected: () => void;
  initialBrokerId?: string;
}

export function ConnectBrokerSheet({
  open,
  onOpenChange,
  onConnected,
  initialBrokerId,
}: ConnectBrokerSheetProps) {
  const [brokerId, setBrokerId] = useState(initialBrokerId ?? 'paper');
  const [connectionName, setConnectionName] = useState('');
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const config = useMemo(() => getBrokerFormConfig(brokerId), [brokerId]);

  useEffect(() => {
    if (!open || !config) return;
    setBrokerId(initialBrokerId ?? config.id);
    setConnectionName((prev) => prev || `${config.label} connection`);
    setFieldValues(defaultFieldValues(config));
    setError(null);
  }, [open, config, initialBrokerId]);

  useEffect(() => {
    const next = getBrokerFormConfig(brokerId);
    if (!next) return;
    setFieldValues(defaultFieldValues(next));
    setConnectionName(`${next.label} connection`);
  }, [brokerId]);

  function updateField(key: string, value: string) {
    setFieldValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!config) return;

    const missing = config.fields.filter(
      (field) => field.required && field.type !== 'checkbox' && !fieldValues[field.key]?.trim(),
    );
    if (!connectionName.trim() || missing.length > 0) {
      setError('Fill in all required fields.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const connection = await createBrokerConnection({
        broker: config.id,
        name: connectionName.trim(),
        credentials: config.buildCredentials(fieldValues),
      });
      await connectBroker(connection.id);
      onConnected();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to connect broker');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="text-left">
          <SheetTitle>Connect broker</SheetTitle>
        </SheetHeader>

        <form onSubmit={(e) => void handleSubmit(e)} className="mt-6 space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Broker</label>
            <div className="grid gap-2">
              {ONBOARDING_BROKERS.map((broker) => (
                <button
                  key={broker.id}
                  type="button"
                  onClick={() => {
                    setBrokerId(broker.id);
                  }}
                  className={cn(
                    'rounded-lg border p-3 text-left transition-colors',
                    brokerId === broker.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-accent/40',
                  )}
                >
                  <p className="text-sm font-medium">{broker.label}</p>
                  <p className="text-muted-foreground mt-0.5 text-xs">{broker.description}</p>
                </button>
              ))}
            </div>
          </div>

          {config ? (
            <BrokerFields
              config={config}
              connectionName={connectionName}
              fieldValues={fieldValues}
              onConnectionNameChange={setConnectionName}
              onFieldChange={updateField}
            />
          ) : null}

          {error ? <p className="text-sm text-red-400">{error}</p> : null}

          <Button type="submit" className="w-full" disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Connecting…
              </>
            ) : (
              'Connect & sync accounts'
            )}
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function BrokerFields({
  config,
  connectionName,
  fieldValues,
  onConnectionNameChange,
  onFieldChange,
}: {
  config: BrokerFormConfig;
  connectionName: string;
  fieldValues: Record<string, string>;
  onConnectionNameChange: (value: string) => void;
  onFieldChange: (key: string, value: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label htmlFor="connection-name" className="text-sm font-medium">
          Connection name
        </label>
        <Input
          id="connection-name"
          value={connectionName}
          onChange={(e) => {
            onConnectionNameChange(e.target.value);
          }}
          placeholder="My Tradovate account"
          required
        />
      </div>

      {config.fields.map((field) =>
        field.type === 'checkbox' ? (
          <label key={field.key} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={fieldValues[field.key] === 'true'}
              onChange={(e) => {
                onFieldChange(field.key, e.target.checked ? 'true' : 'false');
              }}
              className="rounded border-zinc-600"
            />
            {field.label}
          </label>
        ) : (
          <div key={field.key} className="space-y-2">
            <label htmlFor={field.key} className="text-sm font-medium">
              {field.label}
            </label>
            <Input
              id={field.key}
              type={field.type ?? 'text'}
              value={fieldValues[field.key] ?? ''}
              onChange={(e) => {
                onFieldChange(field.key, e.target.value);
              }}
              placeholder={field.placeholder}
              required={field.required}
            />
          </div>
        ),
      )}
    </div>
  );
}
