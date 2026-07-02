'use client';

import { AlertTriangle, X } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const STORAGE_KEY = 'tf_beta_banner_dismissed';

export function BetaBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(localStorage.getItem(STORAGE_KEY) !== '1');
  }, []);

  if (!visible) {
    return null;
  }

  return (
    <div className="border-b border-amber-500/20 bg-amber-500/10 px-4 py-2.5">
      <div className="mx-auto flex max-w-6xl items-start gap-3 text-sm text-amber-100/90">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
        <p className="flex-1 leading-relaxed">
          <strong className="font-medium text-amber-50">Paper beta.</strong> Use paper accounts to
          validate copy workflows. Live trading carries risk. See our{' '}
          <Link href="/risk-disclosure" className="underline underline-offset-2 hover:text-white">
            risk disclosure
          </Link>
          .
        </p>
        <button
          type="button"
          onClick={() => {
            localStorage.setItem(STORAGE_KEY, '1');
            setVisible(false);
          }}
          className="text-amber-300/80 transition-colors hover:text-white"
          aria-label="Dismiss beta notice"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
