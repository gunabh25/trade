'use client';

import { Activity, Search, Shield } from 'lucide-react';
import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import type {
  AdminAnalytics,
  AdminAuditLog,
  AdminBrokerStatus,
  AdminHealth,
  AdminPermissions,
  AdminSearchResult,
  AdminSubscription,
  AdminSupportTicket,
  AdminUser,
  Announcement,
  FeatureFlag,
  SystemLog,
} from '@tradeflow/types/api';

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Skeleton,
} from '@tradeflow/ui';

import {
  adminSearch,
  assignUserRole,
  createAnnouncement,
  createFeatureFlag,
  deleteAnnouncement,
  deleteFeatureFlag,
  formatDate,
  formatMrr,
  getAdminAnalytics,
  getAdminHealth,
  getAdminPermissions,
  listAdminSubscriptions,
  listAdminUsers,
  listAnnouncements,
  listAuditLogs,
  listBrokerStatus,
  listFeatureFlags,
  listSupportTickets,
  listSystemLogs,
  revokeUserRole,
  toggleFeatureFlag,
  updateAdminSubscription,
  updateAdminUser,
  updateAnnouncement,
  updateSupportTicket,
} from '@/features/admin/api/admin-api';
import {
  AdminPageHeader,
  DataTable,
  StatCard,
  StatusBadge,
} from '@/features/admin/components/admin-ui';
import { EmptyState, FadeInStagger } from '@/features/dashboard/components/motion-primitives';

function LoadingBlock() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

function ErrorBlock({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="p-6">
      <EmptyState
        icon={Activity}
        title={title}
        description={message}
        action={
          <Button size="sm" onClick={onRetry}>
            Retry
          </Button>
        }
      />
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

export function AdminSearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<AdminSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const runSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await adminSearch(query.trim());
      setResults(data.results);
      setSearched(true);
    } finally {
      setLoading(false);
    }
  }, [query]);

  return (
    <div>
      <AdminPageHeader
        title="Search"
        description="Find users, tickets, and resources across the platform."
      />
      <div className="space-y-4 p-4 sm:p-6">
        <div className="flex gap-2">
          <Input
            placeholder="Search by email, subject, or ID…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void runSearch();
            }}
          />
          <Button onClick={() => void runSearch()} disabled={loading || !query.trim()}>
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </div>
        {loading ? <Skeleton className="h-32 w-full" /> : null}
        {searched && results.length === 0 ? (
          <EmptyState icon={Search} title="No results" description="Try a different query." />
        ) : null}
        {results.length > 0 ? (
          <Card>
            <CardContent className="pt-6">
              <DataTable
                columns={['Type', 'Title', 'Details']}
                rows={results.map((r) => [
                  <Badge key={`${r.id}-type`} variant="secondary">
                    {r.type}
                  </Badge>,
                  r.title,
                  r.subtitle ?? '—',
                ])}
              />
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  );
}

export function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listAdminUsers({ page, ...(q ? { q } : {}) });
      setUsers(data.items);
      setTotal(data.meta.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }, [q, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleActive = async (user: AdminUser) => {
    await updateAdminUser(user.id, { is_active: !user.is_active });
    void load();
  };

  const toggleRole = async (user: AdminUser, role: string) => {
    if (user.roles.includes(role)) {
      await revokeUserRole(user.id, role);
    } else {
      await assignUserRole(user.id, role);
    }
    void load();
  };

  if (loading && users.length === 0) return <LoadingBlock />;
  if (error)
    return <ErrorBlock title="Users unavailable" message={error} onRetry={() => void load()} />;

  return (
    <div>
      <AdminPageHeader title="Users" description="Manage accounts, roles, and access." />
      <div className="space-y-4 p-4 sm:p-6">
        <div className="flex gap-2">
          <Input
            placeholder="Filter by email…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
            }}
          />
          <Button
            variant="outline"
            onClick={() => {
              setPage(1);
              void load();
            }}
          >
            Filter
          </Button>
        </div>
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['Email', 'Name', 'Roles', 'Status', 'Actions']}
              rows={users.map((user) => [
                user.email,
                [user.first_name, user.last_name].filter(Boolean).join(' ') || '—',
                user.roles.map((r) => (
                  <Badge key={r} variant="secondary" className="mr-1">
                    {r}
                  </Badge>
                )),
                user.is_active ? (
                  <StatusBadge key="active" value="active" />
                ) : (
                  <StatusBadge key="inactive" value="inactive" />
                ),
                <div key="actions" className="flex flex-wrap gap-1">
                  <Button size="sm" variant="outline" onClick={() => void toggleActive(user)}>
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                  {(['admin', 'support', 'trader'] as const).map((role) => (
                    <Button
                      key={role}
                      size="sm"
                      variant={user.roles.includes(role) ? 'default' : 'outline'}
                      onClick={() => void toggleRole(user, role)}
                    >
                      {user.roles.includes(role) ? `− ${role}` : `+ ${role}`}
                    </Button>
                  ))}
                </div>,
              ])}
              emptyMessage="No users found"
            />
          </CardContent>
        </Card>
        <Pagination page={page} total={total} pageSize={20} onPage={setPage} />
      </div>
    </div>
  );
}

export function AdminSubscriptionsPage() {
  const [items, setItems] = useState<AdminSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await listAdminSubscriptions());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load subscriptions');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const cancelSub = async (sub: AdminSubscription) => {
    await updateAdminSubscription(sub.id, { status: 'canceled' });
    void load();
  };

  if (loading) return <LoadingBlock />;
  if (error)
    return (
      <ErrorBlock title="Subscriptions unavailable" message={error} onRetry={() => void load()} />
    );

  return (
    <div>
      <AdminPageHeader
        title="Subscriptions"
        description="View and manage customer billing subscriptions."
      />
      <div className="p-4 sm:p-6">
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['User', 'Plan', 'Status', 'Trial ends', 'Period end', 'Actions']}
              rows={items.map((sub) => [
                sub.user_email,
                sub.plan_name,
                <StatusBadge key="status" value={sub.status} />,
                formatDate(sub.trial_ends_at),
                formatDate(sub.current_period_end),
                sub.status !== 'canceled' ? (
                  <Button
                    key="cancel"
                    size="sm"
                    variant="outline"
                    onClick={() => void cancelSub(sub)}
                  >
                    Cancel
                  </Button>
                ) : (
                  '—'
                ),
              ])}
              emptyMessage="No subscriptions"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function AdminAuditPage() {
  const [items, setItems] = useState<AdminAuditLog[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listAuditLogs({ page });
      setItems(data.items);
      setTotal(data.meta.total);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && items.length === 0) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader title="Audit Logs" description="Security and admin action history." />
      <div className="p-4 sm:p-6">
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['Time', 'User', 'Action', 'Resource', 'IP']}
              rows={items.map((log) => [
                formatDate(log.created_at),
                log.user_email ?? 'system',
                log.action,
                `${log.resource_type}${log.resource_id ? ` · ${log.resource_id.slice(0, 8)}…` : ''}`,
                log.ip_address ?? '—',
              ])}
              emptyMessage="No audit entries"
            />
          </CardContent>
        </Card>
        <Pagination page={page} total={total} pageSize={50} onPage={setPage} />
      </div>
    </div>
  );
}

export function AdminSupportPage() {
  const [items, setItems] = useState<AdminSupportTicket[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await listSupportTickets());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const setStatus = async (ticket: AdminSupportTicket, status: string) => {
    await updateSupportTicket(ticket.id, { status });
    void load();
  };

  if (loading) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader
        title="Support Tickets"
        description="Track and resolve customer support requests."
      />
      <div className="p-4 sm:p-6">
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['Subject', 'User', 'Priority', 'Status', 'Created', 'Actions']}
              rows={items.map((t) => [
                t.subject,
                t.user_email,
                <StatusBadge key="pri" value={t.priority} />,
                <StatusBadge key="st" value={t.status} />,
                formatDate(t.created_at),
                <div key="act" className="flex gap-1">
                  {(['open', 'in_progress', 'resolved', 'closed'] as const).map((s) => (
                    <Button
                      key={s}
                      size="sm"
                      variant={t.status === s ? 'default' : 'outline'}
                      onClick={() => void setStatus(t, s)}
                    >
                      {s.replace(/_/g, ' ')}
                    </Button>
                  ))}
                </div>,
              ])}
              emptyMessage="No support tickets"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function AdminBrokersPage() {
  const [items, setItems] = useState<AdminBrokerStatus[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await listBrokerStatus());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader
        title="Broker Status"
        description="Live connection health across all accounts."
      />
      <div className="p-4 sm:p-6">
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['User', 'Broker', 'Name', 'Status', 'Live', 'Latency', 'Last error']}
              rows={items.map((b) => [
                b.user_email,
                b.broker,
                b.name,
                <StatusBadge key="st" value={b.status} />,
                b.live_connected === null ? '—' : b.live_connected ? 'Yes' : 'No',
                b.live_latency_ms != null ? `${b.live_latency_ms} ms` : '—',
                b.last_error ?? '—',
              ])}
              emptyMessage="No broker connections"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function AdminFeatureFlagsPage() {
  const [items, setItems] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [key, setKey] = useState('');
  const [name, setName] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await listFeatureFlags());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const create = async () => {
    if (!key.trim() || !name.trim()) return;
    await createFeatureFlag({ key: key.trim(), name: name.trim(), enabled: false });
    setKey('');
    setName('');
    void load();
  };

  if (loading && items.length === 0) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader
        title="Feature Flags"
        description="Toggle platform features without deploys."
      />
      <div className="space-y-4 p-4 sm:p-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Create flag</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Input
              placeholder="key"
              value={key}
              onChange={(e) => {
                setKey(e.target.value);
              }}
            />
            <Input
              placeholder="Display name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
              }}
            />
            <Button onClick={() => void create()}>Add</Button>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['Key', 'Name', 'Enabled', 'Updated', 'Actions']}
              rows={items.map((f) => [
                <code key="k" className="text-xs">
                  {f.key}
                </code>,
                f.name,
                f.enabled ? 'Yes' : 'No',
                formatDate(f.updated_at),
                <div key="a" className="flex gap-1">
                  <Button
                    size="sm"
                    variant={f.enabled ? 'default' : 'outline'}
                    onClick={() => void toggleFeatureFlag(f.key, !f.enabled).then(load)}
                  >
                    {f.enabled ? 'Disable' : 'Enable'}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => void deleteFeatureFlag(f.key).then(load)}
                  >
                    Delete
                  </Button>
                </div>,
              ])}
              emptyMessage="No feature flags"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function AdminAnnouncementsPage() {
  const [items, setItems] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await listAnnouncements());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const create = async () => {
    if (!title.trim() || !body.trim()) return;
    await createAnnouncement({ title: title.trim(), body: body.trim(), status: 'draft' });
    setTitle('');
    setBody('');
    void load();
  };

  const publish = async (item: Announcement) => {
    await updateAnnouncement(item.id, { status: 'published' });
    void load();
  };

  if (loading && items.length === 0) return <LoadingBlock />;

  return (
    <div>
      <AdminPageHeader title="Announcements" description="Broadcast updates to users." />
      <div className="space-y-4 p-4 sm:p-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">New announcement</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Input
              placeholder="Title"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
              }}
            />
            <Input
              placeholder="Body"
              value={body}
              onChange={(e) => {
                setBody(e.target.value);
              }}
            />
            <Button onClick={() => void create()}>Create draft</Button>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['Title', 'Status', 'Created', 'Actions']}
              rows={items.map((a) => [
                a.title,
                <StatusBadge key="s" value={a.status} />,
                formatDate(a.created_at),
                <div key="act" className="flex gap-1">
                  {a.status !== 'published' ? (
                    <Button size="sm" onClick={() => void publish(a)}>
                      Publish
                    </Button>
                  ) : null}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => void deleteAnnouncement(a.id).then(load)}
                  >
                    Delete
                  </Button>
                </div>,
              ])}
              emptyMessage="No announcements"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function AdminAnalyticsPage() {
  const [data, setData] = useState<AdminAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await getAdminAnalytics());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <LoadingBlock />;
  if (!data) return null;

  return (
    <div>
      <AdminPageHeader title="Analytics" description="Platform growth and usage metrics." />
      <FadeInStagger className="space-y-6 p-4 sm:p-6">
        <StatCard label="MRR" value={formatMrr(data.mrr_cents)} />
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Subscriptions by plan</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={['Plan', 'Count']}
                rows={data.subscriptions_by_plan.map((p) => [p.name, String(p.count)])}
                emptyMessage="No data"
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Tickets by status</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={['Status', 'Count']}
                rows={data.tickets_by_status.map((t) => [
                  <StatusBadge key={t.status} value={t.status} />,
                  String(t.count),
                ])}
                emptyMessage="No data"
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Connections by broker</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={['Broker', 'Count']}
                rows={data.connections_by_broker.map((c) => [c.broker, String(c.count)])}
                emptyMessage="No data"
              />
            </CardContent>
          </Card>
        </div>
      </FadeInStagger>
    </div>
  );
}

export function AdminHealthPage() {
  const [data, setData] = useState<AdminHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await getAdminHealth());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <LoadingBlock />;
  if (!data) return null;

  const sections: { label: string; value: Record<string, unknown> }[] = [
    { label: 'Database', value: data.database },
    { label: 'Redis', value: data.redis },
    { label: 'Broker monitor', value: data.broker_monitor },
    { label: 'Celery', value: data.celery },
  ];

  return (
    <div>
      <AdminPageHeader
        title="System Health"
        description={`Environment: ${data.environment} · Version: ${data.version}`}
      />
      <div className="space-y-4 p-4 sm:p-6">
        <div className="flex items-center gap-3">
          <StatusBadge value={data.status} />
          <Button variant="outline" size="sm" onClick={() => void load()}>
            Refresh
          </Button>
        </div>
        {sections.map((section) => (
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
    </div>
  );
}

export function AdminLogsPage() {
  const [items, setItems] = useState<SystemLog[]>([]);
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listSystemLogs({ page, ...(q ? { q } : {}) });
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
      <AdminPageHeader title="Logs" description="Application and system log entries." />
      <div className="space-y-4 p-4 sm:p-6">
        <div className="flex gap-2">
          <Input
            placeholder="Search logs…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
            }}
          />
          <Button
            variant="outline"
            onClick={() => {
              setPage(1);
              void load();
            }}
          >
            Search
          </Button>
        </div>
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={['Time', 'Level', 'Source', 'Message']}
              rows={items.map((log) => [
                formatDate(log.created_at),
                <Badge key="lvl" variant={log.level === 'error' ? 'destructive' : 'secondary'}>
                  {log.level}
                </Badge>,
                log.source,
                log.message,
              ])}
              emptyMessage="No log entries"
            />
          </CardContent>
        </Card>
        <Pagination page={page} total={total} pageSize={50} onPage={setPage} />
      </div>
    </div>
  );
}

export function AdminPermissionsPage() {
  const [data, setData] = useState<AdminPermissions | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await getAdminPermissions());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <LoadingBlock />;
  if (!data) return null;

  return (
    <div>
      <AdminPageHeader title="Permissions" description="Role-based access control matrix." />
      <div className="space-y-4 p-4 sm:p-6">
        {data.roles.map((role) => (
          <Card key={role}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base capitalize">
                <Shield className="h-4 w-4" />
                {role}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {(data.permissions[role] ?? []).length === 0 ? (
                  <span className="text-muted-foreground text-sm">No permissions</span>
                ) : (
                  (data.permissions[role] ?? []).map((perm) => (
                    <Badge key={perm} variant="secondary">
                      {perm}
                    </Badge>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        ))}
        <p className="text-muted-foreground text-sm">
          Assign roles from the{' '}
          <Link href="/admin/users" className="text-primary underline-offset-4 hover:underline">
            Users
          </Link>{' '}
          page.
        </p>
      </div>
    </div>
  );
}
