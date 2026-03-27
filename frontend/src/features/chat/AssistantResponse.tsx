import { cn } from '@/lib/cn';
import { Avatar } from '@/design-system/primitives/Avatar';
import type { ReactNode } from 'react';

interface AssistantResponseProps {
  readonly content: ReactNode;
  readonly timestamp?: Date;
  readonly className?: string;
}

export function AssistantResponse({ content, timestamp, className }: AssistantResponseProps) {
  return (
    <div className={cn('flex items-start gap-3 w-full', className)}>
      <Avatar fallback="AI" size="sm" className="shrink-0 mt-1" />
      <div className="flex flex-col gap-1.5 flex-1 min-w-0">
        <div className="bg-surface-elevated border border-line px-5 py-4 rounded-2xl rounded-tl-md max-w-full">
          <div className="text-body-sm font-body text-content-primary prose prose-sm max-w-none">
            {content}
          </div>
        </div>
        {timestamp && (
          <span className="text-body-xs text-content-tertiary px-1">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>
    </div>
  );
}