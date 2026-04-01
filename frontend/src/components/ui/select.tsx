import * as SelectPrimitive from '@radix-ui/react-select';
import { Check, ChevronDown } from 'lucide-react';
import type { ComponentPropsWithoutRef } from 'react';
import { cn } from '../../lib/utils';

export function Select(props: ComponentPropsWithoutRef<typeof SelectPrimitive.Root>) {
  return <SelectPrimitive.Root {...props} />;
}

export function SelectValue(props: ComponentPropsWithoutRef<typeof SelectPrimitive.Value>) {
  return <SelectPrimitive.Value {...props} />;
}

export function SelectTrigger({ className, children, ...props }: ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>) {
  return (
    <SelectPrimitive.Trigger
      className={cn(
        'flex h-11 w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 shadow-sm outline-none transition-[border-color,box-shadow] data-[placeholder]:text-slate-400 focus-visible:border-sky-500 focus-visible:ring-4 focus-visible:ring-sky-100',
        className
      )}
      {...props}
    >
      {children}
      <SelectPrimitive.Icon>
        <ChevronDown className="h-4 w-4 text-slate-400" aria-hidden="true" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  );
}

export function SelectContent({ className, children, position = 'popper', ...props }: ComponentPropsWithoutRef<typeof SelectPrimitive.Content>) {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        position={position}
        className={cn(
          'z-50 min-w-[8rem] overflow-hidden rounded-2xl border border-slate-200 bg-white p-1.5 text-slate-950 shadow-[0_20px_60px_-24px_rgba(15,23,42,0.25)]',
          position === 'popper' && 'data-[side=bottom]:translate-y-1 data-[side=top]:-translate-y-1',
          className
        )}
        {...props}
      >
        <SelectPrimitive.Viewport className="p-1">{children}</SelectPrimitive.Viewport>
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
}

export function SelectItem({ className, children, ...props }: ComponentPropsWithoutRef<typeof SelectPrimitive.Item>) {
  return (
    <SelectPrimitive.Item
      className={cn(
        'relative flex w-full cursor-default select-none items-center rounded-xl py-2.5 pl-10 pr-3 text-sm outline-none transition-colors data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-950 data-[state=checked]:font-medium',
        className
      )}
      {...props}
    >
      <span className="absolute left-3 flex h-4 w-4 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <Check className="h-4 w-4 text-sky-600" aria-hidden="true" />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
}
