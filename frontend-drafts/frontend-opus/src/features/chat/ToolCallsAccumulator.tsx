import { useState } from 'react';
import { cn } from '@/lib/cn';
import { ToolCallItem, type ToolCall } from './ToolCallItem';
import { Badge } from '@/design-system/primitives/Badge';
import { ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { Button } from '@/design-system/primitives/Button';

interface ToolCallsAccumulatorProps {
  readonly toolCalls: ToolCall[];
  readonly className?: string;
}

export function ToolCallsAccumulator({ toolCalls, className }: ToolCallsAccumulatorProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (toolCalls.length === 0) return null;

  const runningCount = toolCalls.filter((tc) => tc.status === 'running').length;
  const successCount = toolCalls.filter((tc) => tc.status === 'success').length;
  const errorCount = toolCalls.filter((tc) => tc.status === 'error').length;

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsExpanded(!isExpanded)}
        className="self-start -ml-2 text-content-secondary hover:text-content-primary"
        icon={runningCount > 0 ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : undefined}
        iconPosition="left"
      >
        <span className="flex items-center gap-2">
          Tool Calls
          <Badge variant="accent" size="sm">{toolCalls.length}</Badge>
          {successCount > 0 && <Badge variant="success" size="sm">{successCount}</Badge>}
          {errorCount > 0 && <Badge variant="error" size="sm">{errorCount}</Badge>}
          {isExpanded ? (
            <ChevronUp className="w-3.5 h-3.5 ml-1" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 ml-1" />
          )}
        </span>
      </Button>

      {isExpanded && (
        <div className="flex flex-col gap-2 pl-2 border-l-2 border-line">
          {toolCalls.map((toolCall) => (
            <ToolCallItem key={toolCall.id} toolCall={toolCall} />
          ))}
        </div>
      )}
    </div>
  );
}