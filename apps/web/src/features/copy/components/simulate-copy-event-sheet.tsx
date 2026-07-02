'use client';

import { useEffect, useState } from 'react';

import type { CopyGroup } from '@tradeflow/types/api';

import { Button, Input, Sheet, SheetContent, SheetHeader, SheetTitle } from '@tradeflow/ui';

import * as copyApi from '@/features/copy/api/copy-api';
import { ApiClientError } from '@/lib/errors';

export function SimulateCopyEventSheet({
  open,
  onOpenChange,
  group,
  onSimulated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  group: CopyGroup | null;
  onSimulated: () => void;
}) {
  const [symbol, setSymbol] = useState('AAPL');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState('1');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setSymbol('AAPL');
    setSide('buy');
    setQuantity('1');
    setError(null);
    setSuccess(null);
  }, [open, group?.id]);

  async function handleSubmit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!group) return;

    const parsedQuantity = Number(quantity);
    if (!symbol.trim() || !Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setError('Enter a valid symbol and quantity.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const results = await copyApi.simulateCopyEvent(group.id, {
        symbol: symbol.trim().toUpperCase(),
        side,
        order_type: 'market',
        quantity: parsedQuantity,
      });
      setSuccess(`Simulated leader event — ${String(results.length)} follower result(s).`);
      onSimulated();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Simulation failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="text-left">
          <SheetTitle>Simulate leader event</SheetTitle>
        </SheetHeader>

        {group ? (
          <form onSubmit={(event) => void handleSubmit(event)} className="mt-6 space-y-5">
            <p className="text-muted-foreground text-sm">
              Inject a synthetic leader order into <strong>{group.name}</strong> without placing a
              broker order. Useful for testing copy execution.
            </p>

            <div className="space-y-2">
              <label className="text-sm font-medium">Symbol</label>
              <Input
                value={symbol}
                onChange={(e) => {
                  setSymbol(e.target.value);
                }}
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Side</label>
              <div className="grid grid-cols-2 gap-2">
                {(['buy', 'sell'] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => {
                      setSide(value);
                    }}
                    className={`rounded-lg border px-3 py-2 text-sm capitalize ${
                      side === value
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-accent/40'
                    }`}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Quantity</label>
              <Input
                type="number"
                min="0.01"
                step="0.01"
                value={quantity}
                onChange={(e) => {
                  setQuantity(e.target.value);
                }}
                required
              />
            </div>

            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            {success ? <p className="text-sm text-emerald-400">{success}</p> : null}

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? 'Simulating…' : 'Simulate event'}
            </Button>
          </form>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
