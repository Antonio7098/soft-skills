import { Wrench, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import type { AssistantToolCallView } from '@/data/types';
import { classifyTool } from '@/hooks/useAssistantStream';
import { ToolCallItem } from './ToolCallItem';
import { CompactGenerationTool } from './CompactGenerationTool';
import { CompactPracticeTool } from './CompactPracticeTool';

interface ToolCallsAccumulatorProps {
  readonly toolCalls: AssistantToolCallView[];
}

export function ToolCallsAccumulator({ toolCalls }: ToolCallsAccumulatorProps) {
  if (toolCalls.length === 0) return null;

  const running = toolCalls.filter((tc) => tc.status === 'running').length;
  const succeeded = toolCalls.filter((tc) => tc.status === 'completed').length;
  const failed = toolCalls.filter((tc) => tc.status === 'failed').length;
  const total = toolCalls.length;

  return (
    <div className="max-w-[85%] mr-auto">
      {/* Summary header */}
      <div className="flex items-center gap-2 mb-2 px-1">
        <Wrench className="w-3.5 h-3.5 text-content-tertiary" />
        <span className="text-body-xs font-medium text-content-tertiary">
          {running > 0
            ? `Running ${running} of ${total} tool${total !== 1 ? 's' : ''}...`
            : `${total} tool${total !== 1 ? 's' : ''} executed`}
        </span>
        <div className="flex items-center gap-1 ml-auto">
          {succeeded > 0 && (
            <span className="flex items-center gap-0.5 text-body-xs text-status-success">
              <CheckCircle2 className="w-3 h-3" /> {succeeded}
            </span>
          )}
          {failed > 0 && (
            <span className="flex items-center gap-0.5 text-body-xs text-status-error">
              <XCircle className="w-3 h-3" /> {failed}
            </span>
          )}
          {running > 0 && (
            <span className="flex items-center gap-0.5 text-body-xs text-accent">
              <Loader2 className="w-3 h-3 animate-spin" /> {running}
            </span>
          )}
        </div>
      </div>

      {/* Tool call list */}
      <div className="flex flex-col gap-2">
        {toolCalls.map((tc) => {
          const type = classifyTool(tc.tool_name);

          // Route to specialized component for expanded content
          const expandedContent =
            type === 'generation' ? <CompactGenerationTool toolCall={tc} /> :
            type === 'practice' ? <CompactPracticeTool toolCall={tc} /> :
            undefined;

          return (
            <ToolCallItem
              key={tc.id}
              toolCall={tc}
              expandedContent={expandedContent}
            />
          );
        })}
      </div>
    </div>
  );
}
