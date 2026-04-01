import type { InputHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export function Input({ className, type = 'text', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type={type}
      className={cn(
        'flex h-11 w-full rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 shadow-sm outline-none transition-[border-color,box-shadow] placeholder:text-slate-400 focus-visible:border-sky-500 focus-visible:ring-4 focus-visible:ring-sky-100',
        className
      )}
      {...props}
    />
  );
}
