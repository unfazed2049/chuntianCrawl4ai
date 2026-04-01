import type { ReactNode } from 'react';
import { Card, CardContent } from './card';

interface ContentCardProps {
  topBar?: ReactNode;
  title: ReactNode;
  meta?: ReactNode;
  content: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function ContentCard({ topBar, title, meta, content, action, className }: ContentCardProps) {
  return (
    <Card
      className={className ?? 'transition-[transform,box-shadow,border-color] hover:-translate-y-0.5 hover:border-sky-100 hover:shadow-[0_24px_64px_-28px_rgba(37,99,235,0.28)]'}
    >
      <CardContent className="flex h-full flex-col gap-4 p-6">
        {(topBar || action) ? (
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">{topBar}</div>
            {action ? <div className="shrink-0">{action}</div> : null}
          </div>
        ) : null}
        <div className="space-y-3">
          <div>{title}</div>
          {meta ? <div>{meta}</div> : null}
        </div>
        <div className="min-w-0 flex-1 rounded-2xl bg-slate-50 p-4 text-sm leading-7 text-slate-700">{content}</div>
      </CardContent>
    </Card>
  );
}
