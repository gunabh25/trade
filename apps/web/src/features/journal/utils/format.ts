export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatGrade(grade: number | null): string {
  if (grade == null) return '—';
  return `${'★'.repeat(grade)}${'☆'.repeat(5 - grade)}`;
}
