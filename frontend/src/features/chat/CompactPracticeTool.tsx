import { motion } from 'framer-motion';
import {
  CheckCircle2,
  Loader2,
  XCircle,
  Play,
  Target,
  MessageSquare,
  Award,
} from 'lucide-react';
import { Badge } from '@/design-system/primitives/Badge';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { StepIndicator } from '@/design-system/patterns/StepIndicator';
import type { AssistantToolCallView } from '@/data/types';

// ---------------------------------------------------------------------------
// Practice-specific metadata extracted from the tool result
// ---------------------------------------------------------------------------

interface PracticeMeta {
  readonly phase: 'loading' | 'responding' | 'assessing' | 'complete' | 'ended' | 'unknown';
  readonly sessionType: string | null;
  readonly collectionTitle: string | null;
  readonly currentStep: number;
  readonly totalSteps: number;
  readonly score: number | null;
  readonly promptTitle: string | null;
}

function extractPracticeMeta(toolCall: AssistantToolCallView): PracticeMeta {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const result: Record<string, any> = toolCall.result ?? {};
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const practice: Record<string, any> = result['practice'] ?? {};

  const status = practice['status'] as string | undefined;
  const phase = mapPhase(status, toolCall);
  const sessionType = (practice['session_type'] as string | undefined) ?? null;
  const collectionTitle = (practice['collection_title'] as string | undefined) ?? null;
  const currentStep = (practice['current_step'] as number | undefined) ?? 1;
  const totalSteps = (practice['total_steps'] as number | undefined) ?? 1;
  const score = (practice['overall_score'] as number | undefined) ?? null;
  const promptTitle = (practice['current_prompt_title'] as string | undefined) ?? null;

  return { phase, sessionType, collectionTitle, currentStep, totalSteps, score, promptTitle };
}

function mapPhase(
  status: string | undefined,
  toolCall: AssistantToolCallView,
): PracticeMeta['phase'] {
  if (toolCall.tool_name === 'end_active_practice') return 'ended';
  if (toolCall.tool_name === 'submit_active_practice_response') {
    return toolCall.status === 'completed' ? 'complete' : 'assessing';
  }
  if (toolCall.tool_name === 'start_collection_practice') {
    return toolCall.status === 'completed' ? 'responding' : 'loading';
  }
  if (status === 'responding') return 'responding';
  if (status === 'assessing') return 'assessing';
  if (status === 'complete') return 'complete';
  return 'unknown';
}

// ---------------------------------------------------------------------------
// Phase display config
// ---------------------------------------------------------------------------

interface PhaseDisplay {
  readonly label: string;
  readonly color: string;
  readonly bgColor: string;
  readonly icon: React.ReactNode;
  readonly badgeVariant: 'accent' | 'success' | 'warning' | 'info' | 'default' | 'error';
}

function getPhaseDisplay(phase: PracticeMeta['phase']): PhaseDisplay {
  switch (phase) {
    case 'loading':
      return {
        label: 'Preparing Session',
        color: 'text-accent',
        bgColor: 'bg-accent/10',
        icon: <Loader2 className="w-4 h-4 animate-spin" />,
        badgeVariant: 'accent',
      };
    case 'responding':
      return {
        label: 'Awaiting Response',
        color: 'text-status-info',
        bgColor: 'bg-status-info/10',
        icon: <MessageSquare className="w-4 h-4" />,
        badgeVariant: 'info',
      };
    case 'assessing':
      return {
        label: 'Assessing',
        color: 'text-status-warning',
        bgColor: 'bg-status-warning/10',
        icon: <Loader2 className="w-4 h-4 animate-spin" />,
        badgeVariant: 'warning',
      };
    case 'complete':
      return {
        label: 'Assessment Complete',
        color: 'text-status-success',
        bgColor: 'bg-status-success/10',
        icon: <Award className="w-4 h-4" />,
        badgeVariant: 'success',
      };
    case 'ended':
      return {
        label: 'Session Ended',
        color: 'text-content-secondary',
        bgColor: 'bg-surface-secondary',
        icon: <CheckCircle2 className="w-4 h-4" />,
        badgeVariant: 'default',
      };
    default:
      return {
        label: 'Practice Session',
        color: 'text-content-secondary',
        bgColor: 'bg-surface-secondary',
        icon: <Play className="w-4 h-4" />,
        badgeVariant: 'default',
      };
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface CompactPracticeToolProps {
  readonly toolCall: AssistantToolCallView;
}

export function CompactPracticeTool({ toolCall }: CompactPracticeToolProps) {
  const meta = extractPracticeMeta(toolCall);
  const phaseDisplay = getPhaseDisplay(meta.phase);
  const isRunning = toolCall.status === 'running';
  const isFailed = toolCall.status === 'failed';

  const progressValue =
    meta.phase === 'complete' || meta.phase === 'ended'
      ? 100
      : meta.totalSteps > 0
        ? (meta.currentStep / meta.totalSteps) * 100
        : 0;

  return (
    <div className="flex flex-col gap-3 pt-2">
      {/* Phase status row */}
      <div className="flex items-center gap-3">
        <div className={`shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${phaseDisplay.bgColor} ${phaseDisplay.color}`}>
          {phaseDisplay.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-body-sm font-medium ${phaseDisplay.color}`}>
            {phaseDisplay.label}
          </p>
          {meta.collectionTitle && (
            <p className="text-body-xs text-content-tertiary truncate">{meta.collectionTitle}</p>
          )}
        </div>
        <Badge variant={phaseDisplay.badgeVariant} size="sm">
          {meta.sessionType ?? 'Practice'}
        </Badge>
      </div>

      {/* Step progress */}
      {meta.totalSteps > 1 && (
        <div className="flex items-center gap-3">
          <StepIndicator current={meta.currentStep} total={meta.totalSteps} label="Progress" />
        </div>
      )}

      {/* Current prompt */}
      {meta.promptTitle && (
        <div className="p-2.5 rounded-lg bg-surface-secondary/60 border border-line/50">
          <div className="flex items-center gap-2">
            <Target className="w-3.5 h-3.5 text-accent shrink-0" />
            <span className="text-body-xs font-medium text-content-primary truncate">
              {meta.promptTitle}
            </span>
          </div>
        </div>
      )}

      {/* Progress bar */}
      {(meta.phase === 'responding' || meta.phase === 'assessing') && (
        <ProgressBar
          value={progressValue}
          variant="accent"
          size="sm"
        />
      )}

      {/* Score display */}
      {meta.score !== null && meta.phase === 'complete' && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-status-success/5 border border-status-success/20">
          <div className="w-10 h-10 rounded-full bg-status-success/10 flex items-center justify-center">
            <span className="text-body-lg font-bold text-status-success">{meta.score}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-body-sm font-medium text-status-success">Score</span>
            <span className="text-body-xs text-content-secondary">Assessment complete</span>
          </div>
        </div>
      )}

      {/* Running indicator */}
      {isRunning && (
        <div className="flex items-center gap-2">
          <Loader2 className="w-3 h-3 text-accent animate-spin" />
          <span className="text-body-xs text-accent">Processing...</span>
          <div className="flex items-center gap-0.5 ml-auto">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                className="w-1 h-1 rounded-full bg-accent"
              />
            ))}
          </div>
        </div>
      )}

      {/* Error state */}
      {isFailed && toolCall.error_message && (
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-status-error/5 border border-status-error/20">
          <XCircle className="w-4 h-4 text-status-error shrink-0 mt-0.5" />
          <span className="text-body-xs text-status-error">{toolCall.error_message}</span>
        </div>
      )}
    </div>
  );
}
