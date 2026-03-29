import { useCallback, useReducer, useRef } from 'react';
import type {
  AssistantSessionView,
  AssistantTurnView,
  AssistantMessageView,
  AssistantToolCallView,
} from '@/data/types';
import { useData } from '@/data';

// ---------------------------------------------------------------------------
// Tool classification — drives which UI component renders the tool call
// ---------------------------------------------------------------------------

export type ToolDisplayType = 'normal' | 'generation' | 'practice';

const GENERATION_TOOLS = new Set(['generate_collection', 'generate_prompt_items']);
const PRACTICE_TOOLS = new Set([
  'start_collection_practice',
  'get_active_practice',
  'submit_active_practice_response',
  'end_active_practice',
]);

export function classifyTool(toolName: string): ToolDisplayType {
  if (GENERATION_TOOLS.has(toolName)) return 'generation';
  if (PRACTICE_TOOLS.has(toolName)) return 'practice';
  return 'normal';
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

export interface AssistantChatState {
  /** Currently active session */
  readonly session: AssistantSessionView | null;
  /** All sessions for session-picker sidebar */
  readonly sessions: AssistantSessionView[];
  /** Turn history for the active session */
  readonly turns: AssistantTurnView[];
  /** Flattened message list for the active session (includes optimistic) */
  readonly messages: AssistantMessageView[];
  /** Tool calls for the currently-streaming turn */
  readonly activeToolCalls: AssistantToolCallView[];
  /** The turn currently being streamed / awaited */
  readonly activeTurn: AssistantTurnView | null;
  /** High-level status */
  readonly status: 'idle' | 'loading' | 'streaming' | 'error';
  readonly error: string | null;
}

const INITIAL_STATE: AssistantChatState = {
  session: null,
  sessions: [],
  turns: [],
  messages: [],
  activeToolCalls: [],
  activeTurn: null,
  status: 'idle',
  error: null,
};

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

type Action =
  | { type: 'SET_SESSIONS'; sessions: AssistantSessionView[] }
  | { type: 'SET_SESSION'; session: AssistantSessionView }
  | { type: 'ADD_OPTIMISTIC_MESSAGE'; message: AssistantMessageView }
  | { type: 'TURN_CREATED'; turn: AssistantTurnView }
  | { type: 'TOOL_STARTED'; toolCall: AssistantToolCallView }
  | { type: 'TOOL_UPDATED'; toolCall: AssistantToolCallView }
  | { type: 'TURN_COMPLETED'; turn: AssistantTurnView }
  | { type: 'TURN_FAILED'; error: string }
  | { type: 'SET_LOADING' }
  | { type: 'SET_ERROR'; error: string }
  | { type: 'CLEAR_ERROR' }
  | { type: 'RESET' };

function reducer(state: AssistantChatState, action: Action): AssistantChatState {
  switch (action.type) {
    case 'SET_SESSIONS':
      return { ...state, sessions: action.sessions };

    case 'SET_SESSION':
      return {
        ...state,
        session: action.session,
        turns: action.session.turns,
        messages: action.session.messages,
        activeToolCalls: [],
        activeTurn: null,
        status: 'idle',
        error: null,
      };

    case 'ADD_OPTIMISTIC_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.message],
        status: 'streaming',
      };

    case 'TURN_CREATED':
      return {
        ...state,
        turns: [...state.turns, action.turn],
        activeTurn: action.turn,
        activeToolCalls: [],
        status: 'streaming',
      };

    case 'TOOL_STARTED':
      return {
        ...state,
        turns: state.activeTurn
          ? state.turns.map((turn) =>
              turn.id === state.activeTurn?.id
                ? { ...turn, tool_calls: [...turn.tool_calls, action.toolCall] }
                : turn,
            )
          : state.turns,
        activeTurn: state.activeTurn
          ? { ...state.activeTurn, tool_calls: [...state.activeTurn.tool_calls, action.toolCall] }
          : state.activeTurn,
        activeToolCalls: [...state.activeToolCalls, action.toolCall],
      };

    case 'TOOL_UPDATED': {
      const idx = state.activeToolCalls.findIndex((tc) => tc.id === action.toolCall.id);
      const nextActiveToolCalls = idx === -1
        ? [...state.activeToolCalls, action.toolCall]
        : state.activeToolCalls.map((toolCall, toolIdx) =>
            toolIdx === idx ? action.toolCall : toolCall,
          );

      const nextTurns = state.activeTurn
        ? state.turns.map((turn) =>
            turn.id === state.activeTurn?.id
              ? {
                  ...turn,
                  tool_calls: turn.tool_calls.some((toolCall) => toolCall.id === action.toolCall.id)
                    ? turn.tool_calls.map((toolCall) =>
                        toolCall.id === action.toolCall.id ? action.toolCall : toolCall,
                      )
                    : [...turn.tool_calls, action.toolCall],
                }
              : turn,
          )
        : state.turns;

      const nextActiveTurn = state.activeTurn
        ? {
            ...state.activeTurn,
            tool_calls: state.activeTurn.tool_calls.some((toolCall) => toolCall.id === action.toolCall.id)
              ? state.activeTurn.tool_calls.map((toolCall) =>
                  toolCall.id === action.toolCall.id ? action.toolCall : toolCall,
                )
              : [...state.activeTurn.tool_calls, action.toolCall],
          }
        : state.activeTurn;

      return {
        ...state,
        turns: nextTurns,
        activeTurn: nextActiveTurn,
        activeToolCalls: nextActiveToolCalls,
      };
    }

    case 'TURN_COMPLETED': {
      const assistantMsg = action.turn.messages.find((m) => m.role === 'assistant');
      const updatedMessages = assistantMsg
        ? [...state.messages, assistantMsg]
        : state.messages;

      return {
        ...state,
        turns: state.turns.map((turn) => (turn.id === action.turn.id ? action.turn : turn)),
        messages: updatedMessages,
        activeTurn: null,
        activeToolCalls: [],
        status: 'idle',
      };
    }

    case 'TURN_FAILED':
      return { ...state, status: 'error', error: action.error };

    case 'SET_LOADING':
      return { ...state, status: 'loading', error: null };

    case 'SET_ERROR':
      return { ...state, status: 'error', error: action.error };

    case 'CLEAR_ERROR':
      return { ...state, error: null };

    case 'RESET':
      return INITIAL_STATE;

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAssistantChat() {
  const data = useData();
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const cleanupRef = useRef<(() => void) | null>(null);

  // ---- Session management ------------------------------------------------

  const loadSessions = useCallback(async () => {
    dispatch({ type: 'SET_LOADING' });
    try {
      const sessions = await data.listAssistantSessions();
      dispatch({ type: 'SET_SESSIONS', sessions });
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: err instanceof Error ? err.message : 'Failed to load sessions' });
      throw err;
    }
  }, [data]);

  const createSession = useCallback(async (title?: string) => {
    dispatch({ type: 'SET_LOADING' });
    try {
      const session = await data.createAssistantSession({ title });
      dispatch({ type: 'SET_SESSION', session });
      // Refresh sessions list
      const sessions = await data.listAssistantSessions();
      dispatch({ type: 'SET_SESSIONS', sessions });
      return session;
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: err instanceof Error ? err.message : 'Failed to create session' });
      throw err;
    }
  }, [data]);

  const selectSession = useCallback(async (sessionId: string) => {
    dispatch({ type: 'SET_LOADING' });
    try {
      const session = await data.getAssistantSession(sessionId);
      dispatch({ type: 'SET_SESSION', session });
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: err instanceof Error ? err.message : 'Failed to load session' });
      throw err;
    }
  }, [data]);

  // ---- Turn management ---------------------------------------------------

  const sendMessage = useCallback(async (message: string, sessionIdOverride?: string) => {
    const targetSessionId = sessionIdOverride ?? state.session?.id;
    if (!targetSessionId) {
      throw new Error('No active session — create or select one first');
    }

    // Optimistic user message
    const optimisticMsg: AssistantMessageView = {
      id: `optimistic-${Date.now()}`,
      turn_id: '',
      role: 'user',
      content: message,
      metadata: {},
      created_at: new Date().toISOString(),
    };
    dispatch({ type: 'ADD_OPTIMISTIC_MESSAGE', message: optimisticMsg });

    try {
      const turn = await data.createAssistantTurn(targetSessionId, { message });
      dispatch({ type: 'TURN_CREATED', turn });

      // Start streaming
      cleanupRef.current?.();
      cleanupRef.current = data.streamAssistantTurn(turn.stream_token, {
        onToolStarted: (tc) => dispatch({ type: 'TOOL_STARTED', toolCall: tc }),
        onToolCompleted: (tc) => dispatch({ type: 'TOOL_UPDATED', toolCall: tc }),
        onToolFailed: (tc) => dispatch({ type: 'TOOL_UPDATED', toolCall: tc }),
        onTurnCompleted: (completedTurn) => dispatch({ type: 'TURN_COMPLETED', turn: completedTurn }),
        onError: (error) => dispatch({ type: 'TURN_FAILED', error }),
        onClose: () => { cleanupRef.current = null; },
      });
    } catch (err) {
      dispatch({ type: 'TURN_FAILED', error: err instanceof Error ? err.message : 'Failed to send message' });
      throw err;
    }
  }, [data, state.session]);

  const cancelTurn = useCallback(async () => {
    if (!state.activeTurn) return;
    try {
      await data.cancelAssistantTurn(state.activeTurn.id, { reason: 'user_requested' });
      cleanupRef.current?.();
      cleanupRef.current = null;
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: err instanceof Error ? err.message : 'Failed to cancel' });
    }
  }, [data, state.activeTurn]);

  const clearError = useCallback(() => dispatch({ type: 'CLEAR_ERROR' }), []);

  return {
    state,
    loadSessions,
    createSession,
    selectSession,
    sendMessage,
    cancelTurn,
    clearError,
  } as const;
}
