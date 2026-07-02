import { StatusPageContent } from '@/features/health/components/status-page';

export const metadata = {
  title: 'System Status — TradeFlow AI',
  description: 'TradeFlow AI platform health and uptime status.',
};

export default function StatusPage() {
  return <StatusPageContent />;
}
