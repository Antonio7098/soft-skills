import { cn } from '@/lib/cn';
import { Badge } from '@/design-system/primitives/Badge';
import { Wrench } from 'lucide-react';

export interface ToolCall {
  readonly id: string;
  readonly name: string;
  readonly description?: string;
  readonly status: 'running' | 'success' | 'error';
  readonly input?: Record<string, unknown>;
  readonly output?: unknown;
  readonly duration?: string;
}

interface ToolCallItemProps {
  readonly toolCall: ToolCall;
  readonly className?: string;
}

export function ToolCallItem({ toolCall, className }: ToolCallItemProps) {
  const statusColors = {
    running: 'text-status-info',
    success: 'text-status-success',
    error: 'text-status-error',
  };

  const statusBadgeVariants = {
    running: 'info' as const,
    success: 'success' as const,
    error: 'error' as const,
  };

  return (
    <div className={cn('flex flex-col gap-2 p-3 rounded-lg bg-surface-secondary/50 border border-line', className)}>
      <div className="flex items-center gap-2">
        <Wrench className={cn('w-3.5 h-3.5', statusColors[toolCall.status])} />
        <span className="text-body-sm font-medium text-content-primary font-mono">
          {toolCall.name}
        </span>
        <Badge variant={statusBadgeVariants[toolCall.status]} size="sm">
          {toolCall.status}
        </Badge>
        {toolCall.duration && (
          <span className="text-body-xs text-content-tertiary ml-auto">
            {toolCall.duration}
          </span>
        )}
      </div>
      {toolCall.description && (
        <p className="text-body-xs text-content-secondary pl-5">
          {toolCall.description}
        </p>
      )}
    </div>
  );
}