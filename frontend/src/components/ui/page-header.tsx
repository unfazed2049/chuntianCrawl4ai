import type { ReactNode } from 'react';
import { Card, CardContent } from './card';

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description: string;
  stats?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, stats, actions }: PageHeaderProps) {
  return (
    <Card>
      <CardContent className="p-6 lg:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-sky-600">{eyebrow}</p>
            <h2 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-slate-950 lg:text-4xl">
              {title}
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 lg:text-base">{description}</p>
            {actions ? <div className="mt-5">{actions}</div> : null}
          </div>
          {stats ? <div className="grid gap-3 sm:grid-cols-3 lg:min-w-[360px]">{stats}</div> : null}
        </div>
      </CardContent>
    </Card>
  );
}
