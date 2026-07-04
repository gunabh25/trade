import { Suspense } from 'react';

import { AuthThemeBar } from '@/components/auth-theme-bar';
import { AuthMarketingPanel } from '@/features/auth/components/auth-marketing-panel';
import { LoginForm } from '@/features/auth/components/login-form';

export default function LoginPage() {
  return (
    <div className="bg-background relative flex min-h-screen">
      <AuthThemeBar />
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 sm:px-12">
        <Suspense fallback={<div className="text-muted-foreground text-sm">Loading…</div>}>
          <LoginForm />
        </Suspense>
      </div>
      <div className="hidden w-[45%] max-w-xl lg:block xl:max-w-2xl">
        <AuthMarketingPanel />
      </div>
    </div>
  );
}
