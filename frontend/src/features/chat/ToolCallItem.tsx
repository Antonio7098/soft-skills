import { useState, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  Wrench,
  FolderOpen,
  Search,
  History,
  Play,
  Eye,
  MessageSquare,
  StopCircle,
  Sparkles,
  FileText,
} from 'lucide-react';
import type { AssistantToolCallView } from '@/data/types';
import { classifyTool } from '@/hooks/useAssistantStream';
import { cn } from '@/lib/cn';

// ---------------------------------------------------------------------------
// Tool metadata — human-friendly labels, icons, and descriptions
// ---------------------------------------------------------------------------

interface ToolMeta {
  readonly label: string;
  readonly description: string;
  readonly icon: ReactNode;
}

const TOOL_META: Record<string, ToolMeta> = {
  list_collections: {
    label: 'Browsing Collections',
    description: 'Searching your practice collections',
    icon: <FolderOpen className="w-4 h-4" />,
  },
  get_collection: {
    label: 'Reading Collection',
    description: 'Loading collection details',
    icon: <Eye className="w-4 h-4" />,
  },
  list_recent_attempts: {
    label: 'Checking History',
    description: 'Reviewing your recent attempts',
    icon: <History className="w-4 h-4" />,
  },
  get_attempt: {
    label: 'Loading Attempt',
    description: 'Fetching attempt details',
    icon: <Search className="w-4 h-4" />,
  },
  start_collection_practice: {
    label: 'Starting Practice',
    description: 'Preparing a new practice session',
    icon: <Play className="w-4 h-4" />,
  },
  get_active_practice: {
    label: 'Checking Practice',
    description: 'Loading current practice session',
    icon: <Eye className="w-4 h-4" />,
  },
  submit_active_practice_response: {
    label: 'Submitting Response',
    description: 'Sending your answer for assessment',
    icon: <MessageSquare className="w-4 h-4" />,
  },
  end_active_practice: {
    label: 'Ending Practice',
    description: 'Wrapping up the practice session',
    icon: <StopCircle className="w-4 h-4" />,
  },
  generate_collection: {
    label: 'Generating Collection',
    description: 'Creating new practice content with AI',
    icon: <Sparkles className="w-4 h-4" />,
  },
  generate_prompt_items: {
    label: 'Generating Prompts',
    description: 'Creating new practice questions',
    icon: <FileText className="w-4 h-4" />,
  },
};

const FALLBACK_META: ToolMeta = {
  label: 'Running Tool',
  description: 'Executing an action',
  icon: <Wrench className="w-4 h-4" />,
};

// ---------------------------------------------------------------------------
// Status indicator
// ---------------------------------------------------------------------------

function StatusIcon({ status }: { status: AssistantToolCallView['status'] }) {
  switch (status) {
    case 'running':
      return <Loader2 className="w-4 h-4 text-accent animate-spin" />;
    case 'completed':
      return <CheckCircle2 className="w-4 h-4 text-status-success" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-status-error" />;
    case 'cancelled':
      return <XCircle className="w-4 h-4 text-content-tertiary" />;
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// Elapsed time helper
// ---------------------------------------------------------------------------

function formatElapsed(startedAt: string, completedAt: string | null): string {
  const start = new Date(startedAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  const ms = end - start;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface ToolCallItemProps {
  readonly toolCall: AssistantToolCallView;
  /** Optional custom expanded content (used by specialized tool components) */
  readonly expandedContent?: ReactNode;
}

export function ToolCallItem({ toolCall, expandedContent }: ToolCallItemProps) {
  const meta = TOOL_META[toolCall.tool_name] ?? FALLBACK_META;
  const displayType = classifyTool(toolCall.tool_name);
  const isExpandable = displayType !== 'normal' || !!expandedContent;
  const [expanded, setExpanded] = useState(false);

  const isRunning = toolCall.status === 'running';
  const isFailed = toolCall.status === 'failed';

  return (
    <div
      className={cn(
        'rounded-xl border overflow-hidden transition-all duration-200',
        isRunning
          ? 'border-accent/30 bg-accent/[0.03]'
          : isFailed
            ? 'border-status-error/30 bg-status-error/[0.03]'
            : 'border-line bg-surface-elevated/50',
      )}
    >
      {/* Header — always visible */}
      <button
        onClick={() => isExpandable && setExpanded((p) => !p)}
        disabled={!isExpandable}
        className={cn(
          'flex items-center gap-3 w-full px-4 py-3 text-left',
          'transition-colors duration-150',
          isExpandable && 'hover:bg-surface-secondary/50 cursor-pointer',
        )}
      >
        {/* Icon */}
        <div
          className={cn(
            'shrink-0 w-8 h-8 rounded-lg flex items-center justify-center',
            isRunning ? 'bg-accent/10 text-accent' : isFailed ? 'bg-status-error/10 text-status-error' : 'bg-surface-secondary text-content-secondary',
          )}
        >
          {meta.icon}
        </div>

        {/* Label + description */}
        <div className="flex-1 min-w-0">
          <p className="text-body-sm font-medium text-content-primary truncate">
            {meta.label}
          </p>
          <p className="text-body-xs text-content-tertiary truncate">
            {isFailed ? (toolCall.error_message ?? 'Tool execution failed') : meta.description}
          </p>
        </div>

        {/* Right side: badge + elapsed + chevron */}
        <div className="flex items-center gap-2 shrink-0">
          {toolCall.started_at && (
            <span className="text-body-xs text-content-tertiary font-mono">
              {formatElapsed(toolCall.started_at, toolCall.completed_at)}
            </span>
          )}

          <StatusIcon status={toolCall.status} />

          {isExpandable && (
            <div
              className={cn(
                'transition-transform duration-150',
                expanded && 'rotate-180',
              )}
            >
              <ChevronDown className="w-4 h-4 text-content-tertiary" />
            </div>
          )}
        </div>
      </button>

      {/* Expandable content */}
      <AnimatePresence initial={false}>
        {expanded && isExpandable && (
          <motion.div
            key="expanded"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-1 border-t border-line/50">
              {expandedContent ?? <DefaultExpandedContent toolCall={toolCall} />}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Default expanded content — shows raw args / result for debugging
// ---------------------------------------------------------------------------

function DefaultExpandedContent({ toolCall }: { toolCall: AssistantToolCallView }) {
  return (
    <div className="flex flex-col gap-2 pt-2">
      {toolCall.args && Object.keys(toolCall.args).length > 0 && (
        <div>
          <p className="text-body-xs font-medium text-content-secondary mb-1">Arguments</p>
          <pre className="text-body-xs text-content-tertiary bg-surface-secondary rounded-lg p-2 overflow-x-auto">
            {JSON.stringify(toolCall.args, null, 2)}
          </pre>
        </div>
      )}
      {toolCall.result && (
        <div>
          <p className="text-body-xs font-medium text-content-secondary mb-1">Result</p>
          <pre className="text-body-xs text-content-tertiary bg-surface-secondary rounded-lg p-2 overflow-x-auto max-h-40">
            {JSON.stringify(toolCall.result, null, 2)}
          </pre>
        </div>
      )}
      {toolCall.error_message && (
        <div className="flex items-start gap-2 p-2 rounded-lg bg-status-error/5 border border-status-error/20">
          <XCircle className="w-4 h-4 text-status-error shrink-0 mt-0.5" />
          <p className="text-body-xs text-status-error">{toolCall.error_message}</p>
        </div>
      )}
    </div>
  );
}

export { TOOL_META, type ToolMeta };
