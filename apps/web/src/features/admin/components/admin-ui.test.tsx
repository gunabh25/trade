import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { describe, expect, it, vi } from 'vitest';

import {
  AdminPageHeader,
  DataTable,
  ExportCsvButton,
  FilterBar,
  StatCard,
} from '@/features/admin/components/admin-ui';

describe('AdminPageHeader', () => {
  it('renders title and optional description', () => {
    render(<AdminPageHeader title="Users" description="Manage accounts" />);
    expect(screen.getByRole('heading', { name: 'Users' })).toBeInTheDocument();
    expect(screen.getByText('Manage accounts')).toBeInTheDocument();
  });
});

describe('StatCard', () => {
  it('renders label, value, and hint', () => {
    render(<StatCard label="Active Users" value={42} hint="Last 24h" />);
    expect(screen.getByText('Active Users')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('Last 24h')).toBeInTheDocument();
  });
});

describe('FilterBar', () => {
  it('calls onChange and onSubmit', () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    render(
      <FilterBar
        value="alpha"
        onChange={onChange}
        onSubmit={onSubmit}
        placeholder="Search users"
      />,
    );

    fireEvent.change(screen.getByPlaceholderText('Search users'), {
      target: { value: 'beta' },
    });
    expect(onChange).toHaveBeenCalledWith('beta');

    fireEvent.keyDown(screen.getByPlaceholderText('Search users'), { key: 'Enter' });
    fireEvent.click(screen.getByRole('button', { name: 'Filter' }));
    expect(onSubmit).toHaveBeenCalledTimes(2);
  });
});

describe('ExportCsvButton', () => {
  it('is disabled when there are no rows', () => {
    render(<ExportCsvButton filename="users.csv" headers={['id']} rows={[]} />);
    expect(screen.getByRole('button', { name: /export csv/i })).toBeDisabled();
  });
});

describe('DataTable', () => {
  it('shows empty message when no rows', () => {
    render(<DataTable columns={['Name']} rows={[]} emptyMessage="Nothing here" />);
    expect(screen.getByText('Nothing here')).toBeInTheDocument();
  });

  it('renders table rows', () => {
    render(
      <DataTable
        columns={['Name', 'Email']}
        rows={[
          ['Alice', 'alice@test.com'],
          ['Bob', 'bob@test.com'],
        ]}
      />,
    );
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('bob@test.com')).toBeInTheDocument();
  });
});
