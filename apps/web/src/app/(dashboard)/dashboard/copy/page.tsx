'use client';

import { useSearchParams } from 'next/navigation';

import { CopyTradingPageContent } from '@/features/copy/components/copy-trading-page';

export default function CopyTradingPage() {
  const searchParams = useSearchParams();
  const autoOpenCreate = searchParams.get('create') === '1';

  return <CopyTradingPageContent autoOpenCreate={autoOpenCreate} />;
}
