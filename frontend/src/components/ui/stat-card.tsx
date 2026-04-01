import type { ReactNode } from 'react';

interface StatCardProps {
  label: string;
  value: ReactNode;
}

export function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{label}</div>
      <div className="mt-2 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}
