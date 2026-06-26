'use client';

import { useEffect } from 'react';

interface JournalKeyboardShortcutsProps {
  onSearch: () => void;
  onNewEntry: () => void;
  onImport: () => void;
  onExportCsv: () => void;
  onNavigatePrev: () => void;
  onNavigateNext: () => void;
  enabled?: boolean;
}

export function useJournalKeyboardShortcuts({
  onSearch,
  onNewEntry,
  onImport,
  onExportCsv,
  onNavigatePrev,
  onNavigateNext,
  enabled = true,
}: JournalKeyboardShortcutsProps) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || target?.isContentEditable) return;

      if (event.key === '/') {
        event.preventDefault();
        onSearch();
        return;
      }
      if (event.key === 'n' && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        onNewEntry();
        return;
      }
      if (event.key === 'i' && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        onImport();
        return;
      }
      if (event.key === 'e' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        onExportCsv();
        return;
      }
      if (event.key === 'j') {
        event.preventDefault();
        onNavigateNext();
        return;
      }
      if (event.key === 'k') {
        event.preventDefault();
        onNavigatePrev();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, onExportCsv, onImport, onNavigateNext, onNavigatePrev, onNewEntry, onSearch]);
}
