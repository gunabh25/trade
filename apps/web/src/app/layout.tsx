import '@tradeflow/ui/globals.css';

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import { AuthProvider } from '@/features/auth/components/auth-provider';

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
    <html lang="en" className="dark">
      <body className={`${inter.variable} min-h-screen font-sans antialiased`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
