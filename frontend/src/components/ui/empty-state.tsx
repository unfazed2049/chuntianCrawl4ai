import type { ReactNode } from 'react';
import { Card, CardContent } from './card';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <Card className={className}>
      <CardContent className="flex min-h-64 flex-col items-center justify-center text-center">
        {icon ? <div className="rounded-full bg-slate-100 p-4 text-slate-500">{icon}</div> : null}
        <h3 className="mt-4 text-xl font-semibold text-slate-950">{title}</h3>
        <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>
        {action ? <div className="mt-5">{action}</div> : null}
      </CardContent>
    </Card>
  );
}
