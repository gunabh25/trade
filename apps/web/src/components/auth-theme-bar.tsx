'use client';

import { ThemeToggle } from '@/components/theme-toggle';

export function AuthThemeBar() {
  return (
    <div className="absolute right-4 top-4 z-10 sm:right-6 sm:top-6">
      <ThemeToggle />
    </div>
  );
}
