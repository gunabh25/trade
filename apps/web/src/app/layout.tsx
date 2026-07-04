import '@tradeflow/ui/globals.css';

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import { AuthProvider } from '@/features/auth/components/auth-provider';
import { ThemeProvider } from '@/components/theme-provider';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: {
    default: 'TradeFlow AI',
    template: '%s | TradeFlow AI',
  },
  description:
    'Professional cloud-based multi-account trade copier, risk management, and trading analytics platform.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} bg-background text-foreground min-h-screen font-sans antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
