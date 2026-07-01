'use client';

import { useSearchParams } from 'next/navigation';

import { AccountsPageContent } from '@/features/broker/components/accounts-page';

export default function AccountsPage() {
  const searchParams = useSearchParams();
  const autoOpenConnect = searchParams.get('connect') === '1';

  return <AccountsPageContent autoOpenConnect={autoOpenConnect} />;
}
