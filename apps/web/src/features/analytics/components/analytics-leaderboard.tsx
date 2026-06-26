'use client';

import { Medal, Trophy } from 'lucide-react';

import type { AnalyticsLeaderboardEntry } from '@tradeflow/types/api';

import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  cn,
} from '@tradeflow/ui';

import { formatRatio } from '@/features/analytics/data/mock-analytics-data';
import { PnlText } from '@/features/dashboard/components/motion-primitives';

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <div className="bg-profit/15 text-profit flex h-7 w-7 items-center justify-center rounded-full">
        <Trophy className="h-3.5 w-3.5" />
      </div>
    );
  }
  if (rank <= 3) {
    return (
      <div className="bg-primary/10 text-primary flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold">
        {rank}
      </div>
    );
  }
  return (
    <div className="text-muted-foreground flex h-7 w-7 items-center justify-center text-xs font-medium">
      {rank}
    </div>
  );
}

function LeaderboardTable({
  title,
  description,
  entries,
  showSharpe = false,
}: {
  title: string;
  description: string;
  entries: AnalyticsLeaderboardEntry[];
  showSharpe?: boolean;
}) {
  return (
    <Card className="border-border/60 bg-card/80 shadow-none">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Medal className="text-muted-foreground h-4 w-4" />
          <div>
            <CardTitle className="text-base font-medium">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-border/60 text-muted-foreground border-b text-left text-[11px] uppercase tracking-wider">
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 text-right font-medium">P&L</th>
                <th className="hidden px-4 py-3 text-right font-medium sm:table-cell">Win Rate</th>
                <th className="hidden px-4 py-3 text-right font-medium md:table-cell">PF</th>
                <th className="hidden px-4 py-3 text-right font-medium lg:table-cell">Trades</th>
                {showSharpe ? (
                  <th className="hidden px-4 py-3 text-right font-medium xl:table-cell">Sharpe</th>
                ) : null}
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.id}
                  className={cn(
                    'border-border/40 hover:bg-accent/30 border-b transition-colors last:border-0',
                    entry.rank === 1 && 'bg-profit/[0.03]',
                  )}
                >
                  <td className="px-4 py-3">
                    <RankBadge rank={entry.rank} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium">{entry.name}</div>
                    {entry.subtitle ? (
                      <Badge variant="outline" className="mt-1 text-[10px] font-normal capitalize">
                        {entry.subtitle}
                      </Badge>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    <PnlText value={entry.pnl} />
                  </td>
                  <td className="hidden px-4 py-3 text-right tabular-nums sm:table-cell">
                    {entry.win_rate.toFixed(1)}%
                  </td>
                  <td className="hidden px-4 py-3 text-right tabular-nums md:table-cell">
                    {formatRatio(entry.profit_factor)}
                  </td>
                  <td className="hidden px-4 py-3 text-right tabular-nums lg:table-cell">
                    {entry.trade_count}
                  </td>
                  {showSharpe ? (
                    <td className="hidden px-4 py-3 text-right tabular-nums xl:table-cell">
                      {formatRatio(entry.sharpe_ratio)}
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

export function AccountLeaderboard({ entries }: { entries: AnalyticsLeaderboardEntry[] }) {
  return (
    <LeaderboardTable
      title="Account Leaderboard"
      description="Top performing connected accounts"
      entries={entries}
      showSharpe
    />
  );
}

export function StrategyLeaderboard({ entries }: { entries: AnalyticsLeaderboardEntry[] }) {
  return (
    <LeaderboardTable
      title="Strategy Leaderboard"
      description="Ranked by total realized P&L"
      entries={entries}
    />
  );
}
