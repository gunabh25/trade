'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@tradeflow/ui';
import { useEffect, useState, type ReactNode } from 'react';

interface AsyncListPageProps<T> {
  title: string;
  description: string;
  emptyMessage: string;
  loadItems: () => Promise<T[]>;
  renderItem: (item: T) => ReactNode;
  getKey: (item: T) => string;
}

export function AsyncListPage<T>({
  title,
  description,
  emptyMessage,
  loadItems,
  renderItem,
  getKey,
}: AsyncListPageProps<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void loadItems()
      .then((data) => {
        if (!cancelled) {
          setItems(data);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load data');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [loadItems]);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="text-muted-foreground mt-1 text-sm">{description}</p>
      </div>

      {loading ? (
        <div className="flex min-h-[200px] items-center justify-center">
          <div className="border-muted border-t-foreground h-8 w-8 animate-spin rounded-full border-2" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-red-400">{error}</p>
          </CardContent>
        </Card>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground text-sm">{emptyMessage}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {items.map((item) => (
            <Card key={getKey(item)}>
              <CardContent className="pt-6">{renderItem(item)}</CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

interface SettingsLink {
  href: string;
  title: string;
  description: string;
}

export function SettingsHubPage({ links }: { links: SettingsLink[] }) {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Manage your account, security, and platform preferences.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {links.map((link) => (
          <a key={link.href} href={link.href} className="block">
            <Card className="hover:bg-accent/40 transition-colors">
              <CardHeader>
                <CardTitle className="text-base">{link.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-sm">{link.description}</p>
              </CardContent>
            </Card>
          </a>
        ))}
      </div>
    </div>
  );
}
