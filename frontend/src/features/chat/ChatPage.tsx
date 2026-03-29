import { useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useAssistantChat } from '@/hooks/useAssistantStream';
import { Button } from '@/design-system/primitives/Button';
import { MessageBubble } from './MessageBubble';
import { ToolCallsAccumulator } from './ToolCallsAccumulator';
import { ChatInput } from './ChatInput';
import { SessionModal } from './SessionSidebar';

// ---------------------------------------------------------------------------
// Streaming indicator — minimal animated dots
// ---------------------------------------------------------------------------

function StreamingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      className="flex items-center gap-1.5 py-2"
    >
      <p className="text-body-xs font-semibold uppercase tracking-wider text-content-tertiary mr-2">
        Assistant
      </p>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          animate={{ opacity: [0.3, 0.8, 0.3] }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.2,
            ease: 'easeInOut',
          }}
          className="w-1.5 h-1.5 rounded-full bg-content-tertiary"
        />
      ))}
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Error banner
// ---------------------------------------------------------------------------

function ErrorBanner({
  message,
  onDismiss,
  onRetry,
}: {
  message: string;
  onDismiss: () => void;
  onRetry?: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8, height: 0 }}
      animate={{ opacity: 1, y: 0, height: 'auto' }}
      exit={{ opacity: 0, y: -8, height: 0 }}
      className="mx-4 mb-2"
    >
      <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-status-error/5 border border-status-error/20">
        <AlertTriangle className="w-4 h-4 text-status-error shrink-0" />
        <p className="flex-1 text-body-sm text-status-error">{message}</p>
        {onRetry && (
          <Button variant="ghost" size="sm" onClick={onRetry} icon={<RefreshCw className="w-3.5 h-3.5" />}>
            Retry
          </Button>
        )}
        <button
          onClick={onDismiss}
          className="text-status-error/60 hover:text-status-error text-body-xs font-medium transition-colors"
        >
          Dismiss
        </button>
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Welcome screen — shown when no session is active
// ---------------------------------------------------------------------------

function WelcomeScreen({ onStart }: { onStart: () => void }) {
  const suggestions = [
    'Show me my recent practice attempts',
    'Start a practice session on communication',
    'Generate a new collection about leadership',
    'What collections do I have?',
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="flex-1 flex flex-col items-center justify-center px-6 py-12"
    >
      <h1 className="font-display text-display-lg text-content-primary mb-2">
        What can I help with?
      </h1>
      <p className="text-body-md text-content-secondary text-center max-w-md mb-10">
        Practice, generate content, review your progress, and more.
      </p>

      {/* Suggestion chips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
        {suggestions.map((suggestion, i) => (
          <motion.button
            key={suggestion}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.06, duration: 0.3, ease: 'easeOut' }}
            onClick={onStart}
            className="text-left px-4 py-3 rounded-lg border border-line bg-surface-elevated/50 hover:bg-surface-elevated hover:border-accent/30 transition-all duration-200 text-body-sm text-content-secondary hover:text-content-primary active:scale-[0.98]"
          >
            {suggestion}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main ChatPage
// ---------------------------------------------------------------------------

export function ChatPage() {
  const {
    state,
    loadSessions,
    createSession,
    selectSession,
    sendMessage,
    cancelTurn,
    clearError,
  } = useAssistantChat();

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const shouldStickToBottomRef = useRef(true);
  const previousScrollStateRef = useRef({
    sessionId: null as string | null,
    userCount: 0,
    assistantCount: 0,
    toolCallCount: 0,
  });
  const isStreaming = state.status === 'streaming';

  const isNearBottom = useCallback((element: HTMLDivElement) => {
    const distanceFromBottom = element.scrollHeight - element.scrollTop - element.clientHeight;
    return distanceFromBottom <= 96;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'auto') => {
    const container = scrollContainerRef.current;
    if (!container) return;

    container.scrollTo({ top: container.scrollHeight, behavior });
    shouldStickToBottomRef.current = true;
  }, []);

  const handleMessagesScroll = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    shouldStickToBottomRef.current = isNearBottom(container);
  }, [isNearBottom]);

  const renderedTurns = state.turns;
  const hasSession = !!state.session;
  const hasMessages = renderedTurns.length > 0;

  const renderedContentMetrics = renderedTurns.reduce(
    (metrics, turn) => {
      const userMessage = turn.messages.find((msg) => msg.role === 'user');
      const assistantMessage = turn.messages.find((msg) => msg.role === 'assistant');
      const turnToolCalls = turn.id === state.activeTurn?.id
        ? state.activeToolCalls.length > 0
          ? state.activeToolCalls
          : turn.tool_calls
        : turn.tool_calls;

      return {
        userCount: metrics.userCount + (userMessage ? 1 : 0),
        assistantCount: metrics.assistantCount + (assistantMessage ? 1 : 0),
        toolCallCount: metrics.toolCallCount + turnToolCalls.length,
      };
    },
    { userCount: 0, assistantCount: 0, toolCallCount: 0 },
  );

  // Follow actual rendered content instead of stream state so scroll changes
  // happen when bubbles/tool rows enter the DOM.
  useEffect(() => {
    const previous = previousScrollStateRef.current;
    const sessionId = state.session?.id ?? null;
    const sessionChanged = previous.sessionId !== sessionId;
    const userMessageAdded = renderedContentMetrics.userCount > previous.userCount;
    const assistantMessageAdded = renderedContentMetrics.assistantCount > previous.assistantCount;
    const toolCallCountChanged = renderedContentMetrics.toolCallCount !== previous.toolCallCount;
    const shouldFollow =
      sessionChanged ||
      userMessageAdded ||
      ((assistantMessageAdded || toolCallCountChanged) && shouldStickToBottomRef.current);

    if (shouldFollow) {
      const behavior = userMessageAdded || assistantMessageAdded ? 'smooth' : 'auto';
      scrollToBottom(behavior);
    }

    previousScrollStateRef.current = {
      sessionId,
      userCount: renderedContentMetrics.userCount,
      assistantCount: renderedContentMetrics.assistantCount,
      toolCallCount: renderedContentMetrics.toolCallCount,
    };
  }, [
    state.session?.id,
    renderedContentMetrics.userCount,
    renderedContentMetrics.assistantCount,
    renderedContentMetrics.toolCallCount,
    scrollToBottom,
  ]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions().catch(() => {
      // Error is already dispatched to state
    });
  }, [loadSessions]);

  const handleNewSession = useCallback(async () => {
    try {
      await createSession();
    } catch {
      // Error dispatched to state
    }
  }, [createSession]);

  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      try {
        await selectSession(sessionId);
      } catch {
        // Error dispatched to state
      }
    },
    [selectSession],
  );

  const handleSend = useCallback(
    async (message: string) => {
      let targetSessionId = state.session?.id;

      // Auto-create session if none exists
      if (!targetSessionId) {
        try {
          const createdSession = await createSession();
          targetSessionId = createdSession.id;
        } catch {
          return;
        }
      }
      try {
        await sendMessage(message, targetSessionId);
      } catch {
        // Error dispatched to state
      }
    },
    [state.session, createSession, sendMessage],
  );

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] -m-8 -mt-8 bg-surface-primary">
      {/* Header bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-line">
        <div className="flex items-center gap-3">
          {hasSession ? (
            <p className="text-body-sm font-semibold text-content-primary truncate">
              {state.session?.title ?? 'Chat Session'}
            </p>
          ) : (
            <p className="text-body-sm font-medium text-content-secondary">New Chat</p>
          )}
          {isStreaming && (
            <div className="flex items-center gap-1">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                  className="w-1.5 h-1.5 rounded-full bg-accent"
                />
              ))}
            </div>
          )}
        </div>

        <SessionModal
          sessions={state.sessions}
          activeSessionId={state.session?.id ?? null}
          onSelectSession={handleSelectSession}
          onNewSession={handleNewSession}
          isLoading={false}
        />
      </div>

      {/* Messages area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleMessagesScroll}
        className="flex-1 overflow-y-auto"
      >
        {!hasSession && !hasMessages ? (
          <WelcomeScreen onStart={handleNewSession} />
        ) : (
          <div className="flex flex-col gap-6 px-6 py-6 max-w-3xl mx-auto w-full">
            {renderedTurns.map((turn) => {
              const userMessage = turn.messages.find((msg) => msg.role === 'user');
              const assistantMessage = turn.messages.find((msg) => msg.role === 'assistant');
              const turnToolCalls = turn.id === state.activeTurn?.id
                ? state.activeToolCalls.length > 0
                  ? state.activeToolCalls
                  : turn.tool_calls
                : turn.tool_calls;

              return (
                <div
                  key={turn.id}
                  className="flex flex-col gap-5"
                >
                  {userMessage && (
                    <MessageBubble
                      role={userMessage.role}
                      content={userMessage.content}
                      timestamp={userMessage.created_at}
                    />
                  )}

                  {turnToolCalls.length > 0 && (
                    <ToolCallsAccumulator toolCalls={turnToolCalls} />
                  )}

                  {assistantMessage && (
                    <MessageBubble
                      role={assistantMessage.role}
                      content={assistantMessage.content}
                      timestamp={assistantMessage.created_at}
                    />
                  )}
                </div>
              );
            })}

            {/* Streaming indicator */}
            <AnimatePresence>
              {isStreaming && (!state.activeTurn || state.activeToolCalls.length === 0) && (
                <StreamingIndicator />
              )}
            </AnimatePresence>

          </div>
        )}
      </div>

      {/* Error banner */}
      <AnimatePresence>
        {state.error && (
          <ErrorBanner
            message={state.error}
            onDismiss={clearError}
          />
        )}
      </AnimatePresence>

      {/* Input area */}
      <div className="px-6 pb-4 pt-2 max-w-3xl mx-auto w-full">
        <ChatInput
          onSend={handleSend}
          onCancel={cancelTurn}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}
