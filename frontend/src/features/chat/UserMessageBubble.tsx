import { cn } from '@/lib/cn';
import { Avatar } from '@/design-system/primitives/Avatar';

interface UserMessageBubbleProps {
  readonly message: string;
  readonly timestamp?: Date;
  readonly className?: string;
}

export function UserMessageBubble({ message, timestamp, className }: UserMessageBubbleProps) {
  return (
    <div className={cn('flex items-start gap-3 justify-end', className)}>
      <div className="flex flex-col gap-1.5 items-end max-w-[70%]">
        <div className="bg-accent text-surface-primary px-4 py-3 rounded-2xl rounded-br-md">
          <p className="text-body-sm font-body">{message}</p>
        </div>
        {timestamp && (
          <span className="text-body-xs text-content-tertiary px-1">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>
      <Avatar fallback="You" size="sm" className="shrink-0 mt-1" />
    </div>
  );
}