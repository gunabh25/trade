'use client';

import { Suspense } from 'react';

import { BillingPage } from '@/features/billing/components/billing-page';

function BillingPageFallback() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center p-6">
      <div className="border-muted border-t-foreground h-8 w-8 animate-spin rounded-full border-2" />
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<BillingPageFallback />}>
      <BillingPage />
    </Suspense>
  );
}
