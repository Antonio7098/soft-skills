import { useCallback, useReducer } from 'react';
import type {
  GenerationProgressState,
  GenerationStage,
  GenerationStreamEvent,
  StructuredCollectionGenerationCommand,
  ChatCollectionGenerationCommand,
  BlueprintInfo,
  PromptItemDraft,
} from '@/data/types';
import { useData } from '@/data';

type GenerationAction =
  | { type: 'START'; generation_id: string; stream_token: string }
  | { type: 'EVENT'; event: GenerationStreamEvent }
  | { type: 'SET_BLUEPRINT'; blueprint: BlueprintInfo }
  | { type: 'SET_PROMPT_ITEMS'; prompt_items: PromptItemDraft[] }
  | { type: 'ADD_PROMPT_ITEM'; prompt_item: PromptItemDraft }
  | { type: 'COMPLETE'; collection: GenerationProgressState['collection'] }
  | { type: 'FAIL'; error: string }
  | { type: 'CANCEL' }
  | { type: 'RESET' };

const STAGE_ORDER: GenerationStage[] = [
  'pending',
  'input_guard',
  'blueprint_transform',
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
  collection: null,
  error: null,
};

interface UseGenerationStreamOptions {
  onComplete?: (collection: GenerationProgressState['collection']) => void;
  onError?: (error: string) => void;
}

export function useGenerationStream(options: UseGenerationStreamOptions = {}) {
  const data = useData();
  const [state, dispatch] = useReducer(reducer, initialState);

  const startGeneration = useCallback(
    async (command: StructuredCollectionGenerationCommand | ChatCollectionGenerationCommand) => {
      const isStructured = 'title_hint' in command;

      // Simulate WebSocket streaming with mock events
      const mockStreamToken = `mock_${Date.now()}`;
      const mockGenerationId = `gen_${Date.now()}`;

      dispatch({ type: 'START', generation_id: mockGenerationId, stream_token: mockStreamToken });

      // Simulate blueprint from command
      const mockBlueprint: BlueprintInfo = {
        title: isStructured && 'title_hint' in command ? (command.title_hint || 'Generated Collection') : 'Generated from prompt',
        summary: 'AI-generated content for practice.',
        prompt_items_count: command.counts.quick_practice_prompt_count + command.counts.interview_prompt_count,
        scenarios_count: command.counts.scenario_count,
        model_slug: 'gpt-4',
      };

      // Simulate mock prompts
      const mockPrompts: PromptItemDraft[] = Array.from(
        { length: command.counts.quick_practice_prompt_count + command.counts.interview_prompt_count },
        (_, i) => ({
          title: `Practice Question ${i + 1}`,
          prompt_type: i < command.counts.quick_practice_prompt_count ? 'quick_practice_prompt' : 'interview_prompt',
          difficulty: 'intermediate',
        })
      );

      // Simulate the streaming pipeline stages
      const stagesToSimulate: {
        stage: GenerationStage;
        progress: number;
        delay: number;
        blueprintPayload?: Record<string, unknown>;
      }[] = [
        { stage: 'input_guard', progress: 5, delay: 200 },
        { stage: 'blueprint_transform', progress: 15, delay: 800, blueprintPayload: mockBlueprint as unknown as Record<string, unknown> },
        { stage: 'blueprint_guard', progress: 20, delay: 300 },
      ];

      for (const stageInfo of stagesToSimulate) {
        await new Promise((resolve) => setTimeout(resolve, stageInfo.delay));
        const event: GenerationStreamEvent = {
          event_id: `evt_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          generation_id: mockGenerationId,
          type: 'progress',
          stage: stageInfo.stage,
          sequence_number: stagesToSimulate.indexOf(stageInfo),
          emitted_at: new Date().toISOString(),
          progress_percent: stageInfo.progress,
          payload: stageInfo.blueprintPayload || {},
        };
        dispatch({ type: 'EVENT', event });
        if (stageInfo.blueprintPayload) {
          dispatch({ type: 'SET_BLUEPRINT', blueprint: mockBlueprint });
        }
      }

      // Simulate prompt items one by one
      for (let i = 0; i < mockPrompts.length; i++) {
        const progress = 35 + (i / mockPrompts.length) * 20;
        await new Promise((resolve) => setTimeout(resolve, 400));
        const event: GenerationStreamEvent = {
          event_id: `evt_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          generation_id: mockGenerationId,
          type: 'progress',
          stage: 'prompt_items_work' as GenerationStage,
          sequence_number: stagesToSimulate.length + i,
          emitted_at: new Date().toISOString(),
          progress_percent: progress,
          payload: { title: mockPrompts[i].title, prompt_type: mockPrompts[i].prompt_type, difficulty: mockPrompts[i].difficulty },
        };
        dispatch({ type: 'EVENT', event });
        dispatch({ type: 'ADD_PROMPT_ITEM', prompt_item: mockPrompts[i] });
      }

      const remainingStages: {
        stage: GenerationStage;
        progress: number;
        delay: number;
      }[] = [
        { stage: 'scenarios_work', progress: 60, delay: 500 },
        { stage: 'scenarios_work', progress: 70, delay: 300 },
        { stage: 'assemble_transform', progress: 80, delay: 400 },
        { stage: 'output_guard', progress: 90, delay: 300 },
        { stage: 'persistence_work', progress: 95, delay: 500 },
        { stage: 'persistence_work', progress: 100, delay: 400 },
      ];

      for (const stageInfo of remainingStages) {
        await new Promise((resolve) => setTimeout(resolve, stageInfo.delay));
        const event: GenerationStreamEvent = {
          event_id: `evt_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          generation_id: mockGenerationId,
          type: 'progress',
          stage: stageInfo.stage,
          sequence_number: stagesToSimulate.length + mockPrompts.length + remainingStages.indexOf(stageInfo),
          emitted_at: new Date().toISOString(),
          progress_percent: stageInfo.progress,
          payload: {},
        };
        dispatch({ type: 'EVENT', event });
      }

      // Now call the actual generation
      try {
        const result = isStructured
          ? await data.generateStructuredCollection(command as StructuredCollectionGenerationCommand)
          : await data.generateChatCollection(command as ChatCollectionGenerationCommand);

        dispatch({ type: 'COMPLETE', collection: result.collection });
        options.onComplete?.(result.collection);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Generation failed';
        dispatch({ type: 'FAIL', error: errorMessage });
        options.onError?.(errorMessage);
      }
    },
    [data, options]
  );

  const cancelGeneration = useCallback(() => {
    dispatch({ type: 'CANCEL' });
  }, []);

  const reset = useCallback(() => {
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