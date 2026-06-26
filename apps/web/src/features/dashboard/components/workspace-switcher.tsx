'use client';

import { Check, ChevronsUpDown, Plus } from 'lucide-react';
import { useState } from 'react';

import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  cn,
} from '@tradeflow/ui';

import type { Workspace } from '@/features/dashboard/data/mock-dashboard-data';

interface WorkspaceSwitcherProps {
  workspaces: Workspace[];
  activeWorkspaceId: string;
}

export function WorkspaceSwitcher({ workspaces, activeWorkspaceId }: WorkspaceSwitcherProps) {
  const [activeId, setActiveId] = useState(activeWorkspaceId);
  const active = workspaces.find((ws) => ws.id === activeId) ?? workspaces[0];

  if (!active) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="border-border/60 bg-background/50 hover:bg-accent/50 h-9 w-[200px] justify-between px-3 font-normal"
        >
          <span className="truncate text-left">
            <span className="block truncate text-sm font-medium">{active.name}</span>
          </span>
          <ChevronsUpDown className="text-muted-foreground ml-2 h-4 w-4 shrink-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[220px]">
        <DropdownMenuLabel className="text-muted-foreground text-xs">Workspaces</DropdownMenuLabel>
        {workspaces.map((workspace) => (
          <DropdownMenuItem
            key={workspace.id}
            onClick={() => {
              setActiveId(workspace.id);
            }}
            className="flex items-center justify-between"
          >
            <div>
              <p className="text-sm">{workspace.name}</p>
              <p className="text-muted-foreground text-xs">{workspace.plan}</p>
            </div>
            {workspace.id === activeId ? <Check className="text-foreground h-4 w-4" /> : null}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-muted-foreground">
          <Plus className="mr-2 h-4 w-4" />
          Create workspace
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function HeaderBreadcrumb({ title }: { title: string }) {
  return (
    <div className="hidden sm:block">
      <p className="text-muted-foreground text-xs">Dashboard</p>
      <h1 className={cn('text-sm font-semibold tracking-tight')}>{title}</h1>
    </div>
  );
}
