import type { LivenessResponse } from '@tradeflow/types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@tradeflow/ui';

interface HealthStatusCardProps {
  health: LivenessResponse;
}

export function HealthStatusCard({ health }: HealthStatusCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>API Status</CardTitle>
        <CardDescription>Backend liveness probe</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Status</span>
          <span className="font-medium capitalize text-green-600">{health.status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Service</span>
          <span className="font-medium">{health.service}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Version</span>
          <span className="font-mono">{health.version}</span>
        </div>
      </CardContent>
    </Card>
  );
}
