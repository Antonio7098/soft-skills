import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, XCircle, Loader2, FileText, Zap, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import type { GenerationStage, BlueprintInfo, PromptItemDraft } from '@/data/types';
import { cn } from '@/lib/cn';

interface GenerationStreamPanelProps {
  readonly currentStage: GenerationStage | null;
  readonly stagesCompleted: GenerationStage[];
  readonly progress: number;
  readonly status: 'idle' | 'started' | 'streaming' | 'completed' | 'failed' | 'cancelled';
  readonly stageLabels: Record<GenerationStage, string>;
  readonly blueprint: BlueprintInfo | null;
  readonly promptItems: PromptItemDraft[];
  readonly onCancel?: () => void;
  readonly error?: string | null;
}

const STAGE_ICONS: Record<GenerationStage, string> = {
  pending: '⚡',
  input_guard: '🔍',
  blueprint_transform: '📋',
  blueprint_guard: '✅',
  prompt_items_work: '💬',
  scenarios_work: '🎭',
  assemble_transform: '🔗',
  output_guard: '🛡️',
  persistence_work: '💾',
  completed: '✨',
  failed: '❌',
  cancelled: '🚫',
};

export function GenerationStreamPanel({
  currentStage,
  stagesCompleted,
  progress,
  status,
  stageLabels,
  blueprint,
  promptItems,
  onCancel,
  error,
}: GenerationStreamPanelProps) {
  const [promptsExpanded, setPromptsExpanded] = useState(false);

  const isActive = status === 'started' || status === 'streaming';
  const isComplete = status === 'completed';
  const isFailed = status === 'failed' || status === 'cancelled';

  const currentLabel = currentStage ? stageLabels[currentStage] : 'Initializing';
  const currentIcon = currentStage ? STAGE_ICONS[currentStage] : '⚡';

  const isGeneratingPrompts = currentStage === 'prompt_items_work' && isActive;
  const hasPrompts = promptItems.length > 0;
  const totalPrompts = blueprint?.prompt_items_count ?? promptItems.length;

  return (
    <Card variant="default" padding="lg" className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h3 className="text-body-lg font-semibold text-content-primary">
          {isComplete ? 'Generation Complete!' : isFailed ? 'Generation Failed' : 'Generating...'}
        </h3>
        <p className="text-body-sm text-content-secondary">
          {isComplete
            ? 'Your collection is ready'
            : isFailed
              ? error || 'An error occurred during generation'
              : 'AI is crafting your personalized practice content'}
        </p>
      </div>

      <ProgressBar
        value={progress}
        variant={isComplete ? 'success' : 'accent'}
        size="md"
        showValue
        label="Overall Progress"
      />

      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-body-xs font-medium text-content-tertiary uppercase tracking-wider">
            Current Stage
          </span>
          {isActive && onCancel && (
            <button
              onClick={onCancel}
              className="text-body-xs font-medium text-status-error hover:text-status-error/80 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

        <div
          className={cn(
            'flex items-center gap-4 px-5 py-4 rounded-xl border-2 transition-all duration-300',
            isComplete
              ? 'bg-status-success/10 border-status-success/40'
              : isFailed
                ? 'bg-status-error/10 border-status-error/40'
                : isActive
                  ? 'bg-accent/5 border-accent/30'
                  : 'bg-surface-secondary/50 border-line'
          )}
        >
          <div
            className={cn(
              'w-12 h-12 rounded-xl flex items-center justify-center text-2xl transition-all duration-300',
              isComplete
                ? 'bg-status-success/20'
                : isFailed
                  ? 'bg-status-error/20'
                  : 'bg-accent/20'
            )}
          >
            {isComplete ? (
              <CheckCircle2 className="w-6 h-6 text-status-success" />
            ) : isFailed ? (
              <XCircle className="w-6 h-6 text-status-error" />
            ) : isActive ? (
              <Loader2 className="w-6 h-6 text-accent animate-spin" />
            ) : (
              currentIcon
            )}
          </div>

          <div className="flex flex-col gap-1 flex-1">
            <span
              className={cn(
                'text-body-md font-semibold transition-colors duration-300',
                isComplete
                  ? 'text-status-success'
                  : isFailed
                    ? 'text-status-error'
                    : isActive
                      ? 'text-accent'
                      : 'text-content-tertiary'
              )}
            >
              {isComplete ? 'Complete!' : isFailed ? 'Failed' : currentLabel}
            </span>
            <span
              className={cn(
                'text-body-xs transition-colors duration-300',
                isComplete
                  ? 'text-status-success/70'
                  : isFailed
                    ? 'text-status-error/70'
                    : isActive
                      ? 'text-accent/70'
                      : 'text-content-tertiary/50'
              )}
            >
              {isComplete
                ? 'All stages completed'
                : isFailed
                  ? 'Generation stopped'
                  : isActive
                    ? `${stagesCompleted.length} stage${stagesCompleted.length !== 1 ? 's' : ''} completed`
                    : 'Starting...'}
            </span>
          </div>

          {isActive && (
            <div className="flex items-center gap-1">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                  className="w-1.5 h-1.5 rounded-full bg-accent"
                />
              ))}
            </div>
          )}
        </div>

        {blueprint && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-xl bg-accent/5 border border-accent/20"
          >
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                <FileText className="w-5 h-5 text-accent" />
              </div>
              <div className="flex flex-col gap-1 flex-1 min-w-0">
                <span className="text-body-xs font-medium text-accent uppercase tracking-wider">
                  Blueprint Ready
                </span>
                <h4 className="text-body-md font-semibold text-content-primary truncate">
                  {blueprint.title}
                </h4>
                <p className="text-body-xs text-content-secondary line-clamp-2">
                  {blueprint.summary}
                </p>
                <div className="flex items-center gap-3 pt-1">
                  <span className="text-body-xs text-content-tertiary">
                    {blueprint.prompt_items_count} prompts
                  </span>
                  <span className="text-body-xs text-content-tertiary">•</span>
                  <span className="text-body-xs text-content-tertiary">
                    {blueprint.scenarios_count} scenarios
                  </span>
                  <span className="text-body-xs text-content-tertiary">•</span>
                  <span className="text-body-xs text-accent">
                    {blueprint.model_slug}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {hasPrompts && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-2"
          >
            <button
              onClick={() => setPromptsExpanded(!promptsExpanded)}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all duration-300 w-full text-left',
                promptsExpanded
                  ? 'bg-accent/10 border-accent/40'
                  : 'bg-surface-secondary/50 border-line hover:border-accent/30 hover:bg-surface-secondary'
              )}
            >
              <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                {isGeneratingPrompts ? (
                  <Loader2 className="w-5 h-5 text-accent animate-spin" />
                ) : (
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                )}
              </div>
              <div className="flex flex-col gap-0.5 flex-1">
                <span className="text-body-sm font-semibold text-content-primary">
                  {isGeneratingPrompts ? 'Generating questions' : 'Questions generated'}
                </span>
                <span className="text-body-xs text-content-secondary">
                  {isGeneratingPrompts
                    ? `${promptItems.length} of ${totalPrompts} done`
                    : `${promptItems.length} questions ready`}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {isGeneratingPrompts && (
                  <div className="flex items-center gap-1">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          delay: i * 0.2,
                        }}
                        className="w-1 h-1 rounded-full bg-accent"
                      />
                    ))}
                  </div>
                )}
                {promptItems.length > 0 && (
                  promptsExpanded ? (
                    <ChevronUp className="w-4 h-4 text-content-tertiary" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-content-tertiary" />
                  )
                )}
              </div>
            </button>

            <AnimatePresence>
              {promptsExpanded && promptItems.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="flex flex-col gap-2 pt-2">
                    {promptItems.map((item, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0 }}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg bg-surface-secondary/50 border border-line"
                      >
                        <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                          {item.prompt_type === 'quick_practice_prompt' ? (
                            <Zap className="w-4 h-4 text-accent" />
                          ) : (
                            <MessageSquare className="w-4 h-4 text-accent" />
                          )}
                        </div>
                        <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                          <span className="text-body-sm font-medium text-content-primary truncate">
                            {item.title}
                          </span>
                          <span className="text-body-xs text-content-tertiary capitalize">
                            {item.prompt_type.replace('_', ' ')} • {item.difficulty}
                          </span>
                        </div>
                        <CheckCircle2 className="w-4 h-4 text-status-success" />
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {stagesCompleted.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-body-xs text-content-tertiary">Done:</span>
            {stagesCompleted.map((stage) => (
              <span
                key={stage}
                className="text-xs px-2 py-1 rounded-full bg-status-success/10 text-status-success flex items-center gap-1"
              >
                {STAGE_ICONS[stage]} {stageLabels[stage]}
              </span>
            ))}
          </div>
        )}
      </div>

      {isFailed && error && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-status-error/5 border border-status-error/20">
          <XCircle className="w-5 h-5 text-status-error flex-shrink-0 mt-0.5" />
          <div className="flex flex-col gap-1">
            <span className="text-body-sm font-medium text-status-error">Error</span>
            <span className="text-body-xs text-status-error/80">{error}</span>
          </div>
        </div>
      )}
    </Card>
  );
}