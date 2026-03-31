import { motion } from 'framer-motion';
import { CheckCircle2, Loader2, FileText, Sparkles, Zap, MessageSquare } from 'lucide-react';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { Badge } from '@/design-system/primitives/Badge';
import type { AssistantToolCallView } from '@/data/types';
import type { GenerationStage, BlueprintInfo, PromptItemDraft } from '@/data/types';

// ---------------------------------------------------------------------------
// Generation-specific metadata extracted from the tool result
// ---------------------------------------------------------------------------

interface GenerationMeta {
  readonly blueprint: BlueprintInfo | null;
  readonly promptItems: PromptItemDraft[];
  readonly currentStage: GenerationStage | null;
  readonly progress: number;
}

function extractGenerationMeta(toolCall: AssistantToolCallView): GenerationMeta {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const result: Record<string, any> = toolCall.result ?? {};

  const blueprint: BlueprintInfo | null =
    (result['blueprint'] as BlueprintInfo | undefined) ??
    (result['collection']?.['blueprint'] as BlueprintInfo | undefined) ??
    null;
  const promptItems: PromptItemDraft[] =
    (result['prompt_items'] as PromptItemDraft[] | undefined) ?? [];
  const progress: number =
    (result['progress_percent'] as number | undefined) ??
    (toolCall.status === 'completed' ? 100 : toolCall.status === 'running' ? 35 : 0);
  const currentStage: GenerationStage | null =
    (result['current_stage'] as GenerationStage | undefined) ??
    (toolCall.status === 'running' ? 'prompt_items_work' : null);

  return { blueprint, promptItems, currentStage, progress };
}

// ---------------------------------------------------------------------------
// Stage labels for the compact view
// ---------------------------------------------------------------------------

const STAGE_LABELS: Partial<Record<GenerationStage, string>> = {
  input_guard: 'Validating input',
  blueprint_transform: 'Creating blueprint',
  blueprint_guard: 'Validating blueprint',
  prompt_items_work: 'Generating prompts',
  scenarios_work: 'Generating scenarios',
  assemble_transform: 'Assembling',
  output_guard: 'Validating output',
  persistence_work: 'Saving',
  completed: 'Complete',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface CompactGenerationToolProps {
  readonly toolCall: AssistantToolCallView;
}

export function CompactGenerationTool({ toolCall }: CompactGenerationToolProps) {
  const meta = extractGenerationMeta(toolCall);
  const isRunning = toolCall.status === 'running';
  const isComplete = toolCall.status === 'completed';
  const isFailed = toolCall.status === 'failed';

  const stageLabel = meta.currentStage ? (STAGE_LABELS[meta.currentStage] ?? meta.currentStage) : 'Initializing';

  return (
    <div className="flex flex-col gap-3 pt-2">
      {/* Progress bar */}
      <ProgressBar
        value={meta.progress}
        variant={isComplete ? 'success' : 'accent'}
        size="sm"
        showValue
        label={isRunning ? stageLabel : isComplete ? 'Generation complete' : 'Generation failed'}
      />

      {/* Animated stage indicator */}
      {isRunning && (
        <div className="flex items-center gap-2">
          <Loader2 className="w-3.5 h-3.5 text-accent animate-spin" />
          <span className="text-body-xs text-accent font-medium">{stageLabel}</span>
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

      {/* Blueprint info — appears when ready */}
      {meta.blueprint && (
        <div className="p-3 rounded-lg bg-accent/5 border border-accent/15">
          <div className="flex items-start gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
              <FileText className="w-4 h-4 text-accent" />
            </div>
            <div className="flex flex-col gap-0.5 min-w-0 flex-1">
              <span className="text-body-xs font-medium text-accent uppercase tracking-wider">Blueprint</span>
              <p className="text-body-sm font-semibold text-content-primary truncate">{meta.blueprint.title}</p>
              {meta.blueprint.summary && (
                <p className="text-body-xs text-content-secondary line-clamp-2">{meta.blueprint.summary}</p>
              )}
              <div className="flex items-center gap-2 pt-1">
                <Badge variant="accent" size="sm">
                  <Sparkles className="w-3 h-3 mr-0.5" />
                  {meta.blueprint.prompt_items_count} prompts
                </Badge>
                <Badge variant="info" size="sm">
                  {meta.blueprint.scenarios_count} scenarios
                </Badge>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Prompt items — stream in as they arrive */}
      {meta.promptItems.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <p className="text-body-xs font-medium text-content-secondary">
            Generated Items ({meta.promptItems.length})
          </p>
          <div className="flex flex-col gap-1">
            {meta.promptItems.map((item, i) => (
              <div
                key={i}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-surface-secondary/60"
              >
                {item.prompt_type === 'quick_practice_prompt' ? (
                  <Zap className="w-3 h-3 text-status-success shrink-0" />
                ) : (
                  <MessageSquare className="w-3 h-3 text-accent shrink-0" />
                )}
                <span className="text-body-xs text-content-primary truncate flex-1">{item.title}</span>
                <CheckCircle2 className="w-3 h-3 text-status-success shrink-0" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error state */}
      {isFailed && toolCall.error_message && (
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-status-error/5 border border-status-error/20">
          <span className="text-body-xs text-status-error">{toolCall.error_message}</span>
        </div>
      )}

      {/* Success state */}
      {isComplete && (
        <div className="flex items-center gap-2 p-2.5 rounded-lg bg-status-success/5 border border-status-success/20">
          <CheckCircle2 className="w-4 h-4 text-status-success shrink-0" />
          <span className="text-body-xs font-medium text-status-success">
            Collection generated successfully
          </span>
        </div>
      )}
    </div>
  );
}
