'use client';

import { Activity, ShieldAlert } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import type {
  AdminFailedLogin,
  AdminNotificationDelivery,
  AdminOrganization,
  AdminPlatformMetrics,
  AdminSecurityEvent,
  AdminTradingAccount,
} from '@tradeflow/types/api';

import { Button, Card, CardContent, CardHeader, CardTitle, Input, Skeleton } from '@tradeflow/ui';

import {
  createOrganization,
  formatDate,
  getAdminMetrics,
  listFailedLogins,
  listNotificationDeliveries,
  listOrganizations,
  listSecurityEvents,
  listTradingAccounts,
  updateOrganization,
} from '@/features/admin/api/admin-api';
import { AdminBarChart, AdminLineChart } from '@/features/admin/components/admin-charts';
import {
  AdminPageHeader,
  DataTable,
  ExportCsvButton,
  FilterBar,
  StatCard,
  StatusBadge,
} from '@/features/admin/components/admin-ui';
import { EmptyState } from '@/features/dashboard/components/motion-primitives';

function metricDisplay(value: unknown): string | number {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') return value;
  return '—';
}

function metricNumber(value: unknown): number {
  return typeof value === 'number' ? value : 0;
}

function readHealthStatus(section: unknown): string {
  if (typeof section === 'object' && section !== null && 'status' in section) {
    const status = section.status;
    if (typeof status === 'string') return status;
  }
  return '—';
}

function readApiTotals(apiUsage: Record<string, unknown>): Record<string, number> {
  const totals = apiUsage.totals_by_metric;
  if (typeof totals !== 'object' || totals === null) return {};
  const result: Record<string, number> = {};
  for (const [key, value] of Object.entries(totals)) {
    if (typeof value === 'number') result[key] = value;
  }
  return result;
}

function celeryWorkerCount(celery: Record<string, unknown>): number {
  return Array.isArray(celery.workers) ? celery.workers.length : 0;
}

function LoadingBlock() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

function Pagination({
  page,
  total,
  pageSize,
  onPage,
}: {
  page: number;
  total: number;
  pageSize: number;
  onPage: (page: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-end gap-2 px-4 py-3">
      <Button
        variant="outline"
        size="sm"
        disabled={page <= 1}
        onClick={() => {
          onPage(page - 1);
        }}
      >
        Previous
      </Button>
      <span className="text-muted-foreground text-sm">
        Page {page} of {totalPages}
      </span>
      <Button
        variant="outline"
        size="sm"
        disabled={page >= totalPages}
        onClick={() => {
          onPage(page + 1);
        }}
      >
        Next
      </Button>
    </div>
  );
}

export function AdminOrganizationsPage() {
  const [items, setItems] = useState<AdminOrganization[]>([]);
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listOrganizations({ page, ...(q ? { q } : {}) });
      setItems(data.items);
      setTotal(data.meta.total);
    } finally {
      setLoading(false);
    }
  }, [q, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleCreate = async () => {
    if (!name || !slug) return;
    await createOrganization({ name, slug });
    setName('');
    setSlug('');
    void load();
  };

  if (loading && items.length === 0) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader
        title="Organizations"
        description="Enterprise tenants, plans, and membership."
      />
      <div className="space-y-4 p-4 sm:p-6">
        <FilterBar
          value={q}
          onChange={setQ}
          placeholder="Search organizations…"
          onSubmit={() => {
            setPage(1);
            void load();
          }}
        >
          <ExportCsvButton
            filename="organizations.csv"
            headers={['Name', 'Slug', 'Plan', 'Members', 'Status', 'Created']}
            rows={items.map((o) => [
              o.name,
              o.slug,
              o.plan_code,
              String(o.member_count),
              o.is_active ? 'active' : 'inactive',
              formatDate(o.created_at),
            ])}
          />
        </FilterBar>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Create organization</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 sm:flex-row">
            <Input
              placeholder="Name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
              }}
            />
            <Input
              placeholder="slug"
              value={slug}
              onChange={(e) => {
                setSlug(e.target.value);
              }}
            />
            <Button
              onClick={() => {
                void handleCreate();
              }}
            >
              Create
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['Name', 'Slug', 'Plan', 'Owner', 'Members', 'Status', 'Actions']}
              rows={items.map((org) => [
                org.name,
                org.slug,
                org.plan_code,
                org.owner_email ?? '—',
                String(org.member_count),
                <StatusBadge key="status" value={org.is_active ? 'active' : 'inactive'} />,
                <Button
                  key="toggle"
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    void updateOrganization(org.id, { is_active: !org.is_active }).then(() => {
                      void load();
                    });
                  }}
                >
                  {org.is_active ? 'Deactivate' : 'Activate'}
                </Button>,
              ])}
            />
          </CardContent>
        </Card>
        <Pagination page={page} total={total} pageSize={20} onPage={setPage} />
      </div>
    </div>
  );
}

export function AdminTradingAccountsPage() {
  const [items, setItems] = useState<AdminTradingAccount[]>([]);
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listTradingAccounts({ page, ...(q ? { q } : {}) });
      setItems(data.items);
      setTotal(data.meta.total);
    } finally {
      setLoading(false);
    }
  }, [q, page]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && items.length === 0) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader title="Trading Accounts" description="All platform trading accounts." />
      <div className="space-y-4 p-4 sm:p-6">
        <FilterBar
          value={q}
          onChange={setQ}
          placeholder="Search accounts…"
          onSubmit={() => {
            setPage(1);
            void load();
          }}
        >
          <ExportCsvButton
            filename="trading-accounts.csv"
            headers={['User', 'Name', 'Type', 'Role', 'Status', 'Balance']}
            rows={items.map((a) => [
              a.user_email,
              a.name,
              a.account_type,
              a.account_role,
              a.status,
              a.balance != null ? String(a.balance) : '—',
            ])}
          />
        </FilterBar>
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['User', 'Account', 'Type', 'Role', 'Status', 'Balance', 'Created']}
              rows={items.map((a) => [
                a.user_email,
                a.name,
                a.account_type,
                a.account_role,
                <StatusBadge key="status" value={a.status} />,
                a.balance != null ? `${a.currency} ${a.balance}` : '—',
                formatDate(a.created_at),
              ])}
            />
          </CardContent>
        </Card>
        <Pagination page={page} total={total} pageSize={20} onPage={setPage} />
      </div>
    </div>
  );
}

export function AdminNotificationsPage() {
  const [items, setItems] = useState<AdminNotificationDelivery[]>([]);
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listNotificationDeliveries({
        page,
        ...(status ? { status } : {}),
      });
      setItems(data.items);
      setTotal(data.meta.total);
    } finally {
      setLoading(false);
    }
  }, [status, page]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && items.length === 0) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader
        title="Notifications"
        description="Delivery log across email, push, and messaging channels."
      />
      <div className="space-y-4 p-4 sm:p-6">
        <FilterBar
          value={status}
          onChange={setStatus}
          placeholder="Filter by status…"
          onSubmit={() => {
            void load();
          }}
        >
          <ExportCsvButton
            filename="notification-deliveries.csv"
            headers={['User', 'Event', 'Channel', 'Status', 'Attempts', 'Created']}
            rows={items.map((d) => [
              d.user_email ?? d.user_id,
              d.event_type,
              d.channel,
              d.status,
              String(d.attempts),
              formatDate(d.created_at),
            ])}
          />
        </FilterBar>
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['User', 'Event', 'Channel', 'Status', 'Attempts', 'Error', 'Created']}
              rows={items.map((d) => [
                d.user_email ?? d.user_id.slice(0, 8),
                d.event_type,
                d.channel,
                <StatusBadge key="status" value={d.status} />,
                String(d.attempts),
                d.last_error ?? '—',
                formatDate(d.created_at),
              ])}
            />
          </CardContent>
        </Card>
        <Pagination page={page} total={total} pageSize={50} onPage={setPage} />
      </div>
    </div>
  );
}

export function AdminSecurityPage() {
  const [events, setEvents] = useState<AdminSecurityEvent[]>([]);
  const [failedLogins, setFailedLogins] = useState<AdminFailedLogin[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [eventData, logins] = await Promise.all([
        listSecurityEvents({ page }),
        listFailedLogins(),
      ]);
      setEvents(eventData.items);
      setTotal(eventData.meta.total);
      setFailedLogins(logins);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && events.length === 0) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader
        title="Security"
        description="Security events, failed logins, and lockouts."
      />
      <div className="space-y-4 p-4 sm:p-6">
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard label="Failed login records" value={failedLogins.length} />
          <StatCard label="Active lockouts" value={failedLogins.filter((l) => l.locked).length} />
          <StatCard label="Security events" value={total} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Failed logins & lockouts</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={['Email', 'Locked', 'Attempts', 'Retry after (s)']}
              rows={failedLogins.map((l) => [
                l.email,
                l.locked ? 'Yes' : 'No',
                String(l.recent_attempts),
                l.retry_after_seconds != null ? String(l.retry_after_seconds) : '—',
              ])}
              emptyMessage="No failed login records in Redis"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Security events</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={['Action', 'User', 'Resource', 'IP', 'Time']}
              rows={events.map((e) => [
                e.action,
                e.user_id?.slice(0, 8) ?? '—',
                e.resource_type,
                e.ip_address ?? '—',
                formatDate(e.created_at),
              ])}
            />
          </CardContent>
        </Card>
        <Pagination page={page} total={total} pageSize={50} onPage={setPage} />
      </div>
    </div>
  );
}

export function AdminMetricsPage() {
  const [metrics, setMetrics] = useState<AdminPlatformMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setMetrics(await getAdminMetrics());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <LoadingBlock />;

  if (error || !metrics) {
    return (
      <div className="p-6">
        <EmptyState
          icon={ShieldAlert}
          title="Metrics unavailable"
          description={error ?? ''}
          action={
            <Button size="sm" onClick={() => void load()}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  const apiTotals = readApiTotals(metrics.api_usage);

  return (
    <div>
      <AdminPageHeader
        title="Platform Metrics"
        description="Redis, Celery, queues, API usage, and rate limits."
      />
      <div className="grid gap-4 p-4 sm:grid-cols-2 sm:p-6 xl:grid-cols-4">
        <StatCard label="Redis keys" value={metricDisplay(metrics.redis.keys)} />
        <StatCard label="Celery workers" value={celeryWorkerCount(metrics.celery)} />
        <StatCard
          label="Active rate limits"
          value={metricNumber(metrics.rate_limits.active_rate_limit_keys)}
        />
        <StatCard
          label="Notification pending"
          value={metricNumber(metrics.notifications.pending)}
        />
      </div>

      <div className="grid gap-4 p-4 sm:p-6 lg:grid-cols-2">
        {[
          { label: 'Health', value: metrics.health },
          { label: 'Redis', value: metrics.redis },
          { label: 'Celery', value: metrics.celery },
          { label: 'Queues', value: metrics.queues },
          { label: 'Security', value: metrics.security },
          { label: 'API usage', value: metrics.api_usage },
          { label: 'Rate limits', value: metrics.rate_limits },
          { label: 'Notifications', value: metrics.notifications },
          { label: 'WebSockets', value: metrics.websockets },
        ].map((section) => (
          <Card key={section.label}>
            <CardHeader>
              <CardTitle className="text-base">{section.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted overflow-x-auto rounded-md p-3 text-xs">
                {JSON.stringify(section.value, null, 2)}
              </pre>
            </CardContent>
          </Card>
        ))}
      </div>

      {Object.keys(apiTotals).length > 0 ? (
        <div className="p-4 sm:p-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">API usage by metric</CardTitle>
            </CardHeader>
            <CardContent>
              <AdminBarChart
                data={Object.entries(apiTotals).map(([metric, count]) => ({
                  metric,
                  count,
                }))}
                xKey="metric"
                yKey="count"
              />
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}

export function AdminObservabilityDashboard() {
  const [metrics, setMetrics] = useState<AdminPlatformMetrics | null>(null);

  useEffect(() => {
    getAdminMetrics()
      .then(setMetrics)
      .catch(() => {
        setMetrics(null);
      });
  }, []);

  if (!metrics) return null;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Queue status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>Copy retry: {metricNumber(metrics.queues.copy_retry_items)}</p>
          <p>Usage keys: {metricNumber(metrics.queues.usage_tracking_keys)}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">System health</CardTitle>
        </CardHeader>
        <CardContent>
          <StatusBadge
            value={typeof metrics.health.status === 'string' ? metrics.health.status : 'unknown'}
          />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4" /> Live services
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          <p>DB: {readHealthStatus(metrics.health.database)}</p>
          <p>Redis: {readHealthStatus(metrics.health.redis)}</p>
          <p>Celery: {readHealthStatus(metrics.health.celery_broker)}</p>
        </CardContent>
      </Card>
    </div>
  );
}

export { AdminLineChart };
