import { useCallback, useReducer, useRef } from 'react';
import type {
  GenerationProgressState,
  GenerationStage,
  GenerationStreamEvent,
  StructuredCollectionGenerationCommand,
  ChatCollectionGenerationCommand,
  BlueprintInfo,
  PromptItemDraft,
  GenerationActivityItem,
} from '@/data/types';
import { useData } from '@/data';

type GenerationAction =
  | { type: 'START'; generation_id: string; stream_token: string }
  | { type: 'EVENT'; event: GenerationStreamEvent }
  | { type: 'SET_BLUEPRINT'; blueprint: BlueprintInfo }
  | { type: 'SET_PROMPT_ITEMS'; prompt_items: PromptItemDraft[] }
  | { type: 'ADD_PROMPT_ITEM'; prompt_item: PromptItemDraft }
  | { type: 'ADD_ACTIVITY'; item: GenerationActivityItem }
  | { type: 'COMPLETE'; collection: GenerationProgressState['collection'] }
  | { type: 'FAIL'; error: string }
  | { type: 'CANCEL' }
  | { type: 'RESET' };

const STAGE_ORDER: GenerationStage[] = [
  'pending',
  'input_guard',
  'blueprint_transform',
  'blueprint_llm_transform',
  'blueprint_guard',
  'prompt_items_work',
  'scenarios_work',
  'assemble_transform',
  'output_guard',
  'persistence_work',
  'completed',
];

const STAGE_LABELS: Record<GenerationStage, string> = {
  pending: 'Initializing',
  input_guard: 'Validating input',
  blueprint_transform: 'Creating blueprint',
  blueprint_llm_transform: 'Planning blueprint',
  blueprint_guard: 'Validating blueprint',
  prompt_items_work: 'Generating prompts',
  scenarios_work: 'Generating scenarios',
  assemble_transform: 'Assembling content',
  output_guard: 'Validating output',
  persistence_work: 'Saving collection',
  completed: 'Complete',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

const STAGE_ICONS: Record<GenerationStage, string> = {
  pending: '⚡',
  input_guard: '🔍',
  blueprint_transform: '📋',
  blueprint_llm_transform: '🧠',
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

function reducer(state: GenerationProgressState, action: GenerationAction): GenerationProgressState {
  switch (action.type) {
    case 'START':
      return {
        ...state,
        status: 'started',
        generation_id: action.generation_id,
        stream_token: action.stream_token,
        current_stage: 'pending',
        progress_percent: 2,
        error: null,
        activity: [
          {
            id: `start:${action.generation_id}`,
            stage: 'pending',
            message: 'Starting generation and connecting to live updates.',
            timestamp: new Date().toISOString(),
          },
        ],
      };
    case 'EVENT': {
      const event = action.event;
      const newStagesCompleted =
        event.stage !== 'pending' && event.stage !== 'completed' && event.stage !== 'failed'
          ? state.stages_completed.includes(event.stage)
            ? state.stages_completed
            : [...state.stages_completed, event.stage]
          : state.stages_completed;
      return {
        ...state,
        status: 'streaming',
        current_stage: event.stage,
        progress_percent: event.progress_percent,
        stages_completed: newStagesCompleted,
      };
    }
    case 'SET_BLUEPRINT':
      return {
        ...state,
        blueprint: action.blueprint,
      };
    case 'SET_PROMPT_ITEMS':
      return {
        ...state,
        prompt_items: action.prompt_items,
      };
    case 'ADD_PROMPT_ITEM':
      return {
        ...state,
        prompt_items: [...state.prompt_items, action.prompt_item],
      };
    case 'ADD_ACTIVITY':
      return {
        ...state,
        activity: [action.item, ...state.activity].slice(0, 8),
      };
    case 'COMPLETE':
      return {
        ...state,
        status: 'completed',
        current_stage: 'completed',
        progress_percent: 100,
        collection: action.collection,
        stages_completed: [...state.stages_completed, 'completed'],
      };
    case 'FAIL':
      return {
        ...state,
        status: 'failed',
        current_stage: 'failed',
        error: action.error,
      };
    case 'CANCEL':
      return {
        ...state,
        status: 'cancelled',
        current_stage: 'cancelled',
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

const initialState: GenerationProgressState = {
  status: 'idle',
  generation_id: null,
  stream_token: null,
  stages_completed: [],
  current_stage: null,
  progress_percent: 0,
  blueprint: null,
  prompt_items: [],
  activity: [],
  collection: null,
  error: null,
};

function buildActivityFromEvent(event: GenerationStreamEvent): GenerationActivityItem | null {
  const payload = event.payload as Record<string, unknown>;
  let message: string | null = null;
  switch (event.stage) {
    case 'input_guard':
      message = 'Validated generation request.';
      break;
    case 'blueprint_transform':
      message = 'Prepared blueprint planning request.';
      break;
    case 'blueprint_llm_transform':
      message = typeof payload.title === 'string'
        ? `Planned blueprint: ${payload.title}`
        : 'Blueprint plan generated.';
      break;
    case 'blueprint_guard':
      message = 'Validated the blueprint contract.';
      break;
    case 'prompt_items_work':
      if (Array.isArray(payload.prompt_items) && payload.prompt_items.length > 0) {
        message = `Generated ${payload.prompt_items.length} prompt item${payload.prompt_items.length === 1 ? '' : 's'}.`;
      } else if (typeof payload.generated_prompt_items === 'number') {
        message = `Prompt item workers finished ${payload.generated_prompt_items} item${payload.generated_prompt_items === 1 ? '' : 's'}.`;
      } else {
        message = 'Prompt item workers are running.';
      }
      break;
    case 'scenarios_work':
      message = 'Scenario workers are running.';
      break;
    case 'assemble_transform':
      message = 'Assembling final collection draft.';
      break;
    case 'output_guard':
      message = 'Running final validation.';
      break;
    case 'persistence_work':
      message = 'Saving generated collection.';
      break;
    case 'completed':
      message = 'Generation completed.';
      break;
    case 'failed':
      message = typeof payload.error === 'string' ? payload.error : 'Generation failed.';
      break;
    case 'cancelled':
      message = 'Generation was cancelled.';
      break;
    default:
      message = null;
  }
  if (!message) return null;
  return {
    id: event.event_id,
    stage: event.stage,
    message,
    timestamp: event.emitted_at,
  };
}

interface UseGenerationStreamOptions {
  onComplete?: (collection: GenerationProgressState['collection']) => void;
  onError?: (error: string) => void;
}

export function useGenerationStream(options: UseGenerationStreamOptions = {}) {
  const data = useData();
  const [state, dispatch] = useReducer(reducer, initialState);
  const cleanupRef = useRef<(() => void) | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const GENERATION_TIMEOUT_MS = 600_000;

  const startGeneration = useCallback(
    async (command: StructuredCollectionGenerationCommand | ChatCollectionGenerationCommand) => {
      const isStructured = 'title_hint' in command;
      try {
        cleanupRef.current?.();
        dispatch({ type: 'RESET' });
        dispatch({
          type: 'START',
          generation_id: 'pending',
          stream_token: 'pending',
        });
        const started = isStructured
          ? await data.generateStructuredCollection(command as StructuredCollectionGenerationCommand)
          : await data.generateChatCollection(command as ChatCollectionGenerationCommand);
        dispatch({ type: 'START', generation_id: started.generation_id, stream_token: started.stream_token });

        timeoutRef.current = setTimeout(() => {
          const errorMessage = 'Generation timed out';
          dispatch({ type: 'FAIL', error: errorMessage });
          options.onError?.(errorMessage);
          cleanupRef.current?.();
          cleanupRef.current = null;
        }, GENERATION_TIMEOUT_MS);

        cleanupRef.current = data.streamGeneration(started.stream_token, {
           onEvent: (event: GenerationStreamEvent) => {
            if (timeoutRef.current) {
              clearTimeout(timeoutRef.current);
              timeoutRef.current = setTimeout(() => {
                const errorMessage = 'Generation timed out';
                dispatch({ type: 'FAIL', error: errorMessage });
                options.onError?.(errorMessage);
                cleanupRef.current?.();
                cleanupRef.current = null;
              }, GENERATION_TIMEOUT_MS);
            }
            dispatch({ type: 'EVENT', event });
            const activity = buildActivityFromEvent(event);
            if (activity) {
              dispatch({ type: 'ADD_ACTIVITY', item: activity });
            }
            if (event.stage === 'blueprint_llm_transform') {
              const payload = event.payload as Partial<BlueprintInfo>;
              if (payload.title && payload.summary) {
                dispatch({
                  type: 'SET_BLUEPRINT',
                  blueprint: {
                    title: payload.title,
                    summary: payload.summary,
                    prompt_items_count: Number(payload.prompt_items_count ?? 0),
                    scenarios_count: Number(payload.scenarios_count ?? 0),
                    model_slug: String(payload.model_slug ?? ''),
                  },
                });
              }
            }
            if (event.stage === 'prompt_items_work') {
              const promptItems = Array.isArray(event.payload.prompt_items) ? event.payload.prompt_items : [];
              for (const item of promptItems) {
                const promptItem = item as PromptItemDraft;
                if (promptItem?.title && promptItem?.prompt_type) {
                  dispatch({ type: 'ADD_PROMPT_ITEM', prompt_item: promptItem });
                }
              }
            }
          },
           onCompleted: async (payload: unknown) => {
            if (timeoutRef.current) {
              clearTimeout(timeoutRef.current);
              timeoutRef.current = null;
            }
            cleanupRef.current?.();
            cleanupRef.current = null;
            try {
              const collectionId = typeof payload.collection_id === 'string' ? payload.collection_id : null;
              if (!collectionId) {
                throw new Error('Generation completed without a collection id.');
              }
              const collection = await data.getCollection(collectionId);
              dispatch({ type: 'COMPLETE', collection });
              options.onComplete?.(collection);
            } catch (err) {
              const errorMessage = err instanceof Error ? err.message : 'Failed to load generated collection';
              dispatch({ type: 'FAIL', error: errorMessage });
              options.onError?.(errorMessage);
            }
          },
           onFailed: (payload: unknown) => {
            if (timeoutRef.current) {
              clearTimeout(timeoutRef.current);
              timeoutRef.current = null;
            }
            cleanupRef.current?.();
            cleanupRef.current = null;
            const errorMessage =
              (typeof payload.error === 'string' && payload.error)
              || (typeof payload.reason === 'string' && payload.reason)
              || 'Generation failed';
            dispatch({ type: 'FAIL', error: errorMessage });
            options.onError?.(errorMessage);
          },
           onError: (errorMessage: string) => {
            if (timeoutRef.current) {
              clearTimeout(timeoutRef.current);
              timeoutRef.current = null;
            }
            dispatch({ type: 'FAIL', error: errorMessage });
            options.onError?.(errorMessage);
          },
          onClose: () => {
            if (timeoutRef.current) {
              clearTimeout(timeoutRef.current);
              timeoutRef.current = null;
            }
            cleanupRef.current = null;
            if (state.status !== 'completed' && state.status !== 'failed' && state.status !== 'cancelled') {
              const errorMessage = 'Generation stream closed unexpectedly';
              dispatch({ type: 'FAIL', error: errorMessage });
              options.onError?.(errorMessage);
            }
          },
        });
      } catch (err) {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }
        const errorMessage = err instanceof Error ? err.message : 'Generation failed';
        dispatch({ type: 'FAIL', error: errorMessage });
        options.onError?.(errorMessage);
      }
    },
    [data, options]
  );

  const cancelGeneration = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    cleanupRef.current?.();
    cleanupRef.current = null;
    dispatch({ type: 'CANCEL' });
  }, []);

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    cleanupRef.current?.();
    cleanupRef.current = null;
    dispatch({ type: 'RESET' });
  }, []);

  return {
    state,
    startGeneration,
    cancelGeneration,
    reset,
    stageLabels: STAGE_LABELS,
    stageIcons: STAGE_ICONS,
    stageOrder: STAGE_ORDER,
  };
}

export type { GenerationStage };
export { STAGE_LABELS, STAGE_ICONS, STAGE_ORDER };
