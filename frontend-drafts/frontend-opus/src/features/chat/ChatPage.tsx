import { useState, useRef, useEffect } from 'react';
import { MessageSquare } from 'lucide-react';
import { UserMessageBubble } from './UserMessageBubble';
import { AssistantResponse } from './AssistantResponse';
import { ToolCallsAccumulator } from './ToolCallsAccumulator';
import type { ToolCall } from './ToolCallItem';
import { ChatInput } from './ChatInput';
import { EmptyState } from '@/design-system/patterns/EmptyState';

interface Message {
  readonly id: string;
  readonly type: 'user' | 'assistant';
  readonly content: string;
  readonly timestamp: Date;
}

interface ToolCallGroup {
  readonly id: string;
  readonly toolCalls: ToolCall[];
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [toolCallGroups, setToolCallGroups] = useState<ToolCallGroup[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, toolCallGroups]);

  function simulateAssistantResponse(userMessage: string) {
    const assistantMessageId = `msg-${Date.now()}`;
    const toolGroupId = `tools-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        type: 'assistant',
        content: 'Let me analyze that and help you out.',
        timestamp: new Date(),
      },
    ]);

    const simulatedToolCalls: ToolCall[] = [
      {
        id: `${toolGroupId}-1`,
        name: 'searchKnowledgeBase',
        description: 'Searching for relevant information...',
        status: 'running',
      },
      {
        id: `${toolGroupId}-2`,
        name: 'getContext',
        description: 'Retrieving context about your request',
        status: 'running',
      },
    ];

    setToolCallGroups([{ id: toolGroupId, toolCalls: simulatedToolCalls }]);

    setTimeout(() => {
      setToolCallGroups((prev) =>
        prev.map((group) =>
          group.id === toolGroupId
            ? {
                ...group,
                toolCalls: group.toolCalls.map((tc) =>
                  tc.id === `${toolGroupId}-1` ? { ...tc, status: 'success', duration: '234ms' } : tc
                ),
              }
            : group
        )
      );
    }, 600);

    setTimeout(() => {
      setToolCallGroups((prev) =>
        prev.map((group) =>
          group.id === toolGroupId
            ? {
                ...group,
                toolCalls: group.toolCalls.map((tc) =>
                  tc.id === `${toolGroupId}-2` ? { ...tc, status: 'success', duration: '189ms' } : tc
                ),
              }
            : group
        )
      );
    }, 1200);

    setTimeout(() => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `Based on my analysis of "${userMessage}", I can provide you with a comprehensive response. I've searched through the knowledge base and retrieved the relevant context to give you the best possible answer.

The key points are:
1. First important insight about your query
2. Second consideration to keep in mind
3. A practical recommendation for next steps

Would you like me to elaborate on any of these points?`,
              }
            : msg
        )
      );
      setIsLoading(false);
    }, 2000);
  }

  function handleSendMessage(message: string) {
    const userMessageId = `msg-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      {
        id: userMessageId,
        type: 'user',
        content: message,
        timestamp: new Date(),
      },
    ]);

    setIsLoading(true);
    simulateAssistantResponse(message);
  }

  return (
    <div className="flex flex-col h-full bg-surface-primary">
      <header className="flex items-center gap-3 px-6 py-4 border-b border-line bg-surface-elevated/50">
        <div className="w-10 h-10 rounded-full bg-accent-muted flex items-center justify-center">
          <MessageSquare className="w-5 h-5 text-accent" />
        </div>
        <div className="flex flex-col">
          <h1 className="font-display text-display-sm text-content-primary">Assistant</h1>
          <p className="text-body-xs text-content-secondary">Powered by AI</p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center p-6">
            <EmptyState
              icon={<MessageSquare className="w-6 h-6" />}
              title="Start a conversation"
              description="Send a message to begin chatting with the assistant."
            />
          </div>
        ) : (
          <div className="flex flex-col gap-6 p-6">
            {messages.map((message, index) => {
              const lastGroup = toolCallGroups[toolCallGroups.length - 1];
              return (
                <div key={message.id} className="flex flex-col gap-4">
                  {message.type === 'user' ? (
                    <UserMessageBubble
                      message={message.content}
                      timestamp={message.timestamp}
                    />
                  ) : (
                    <AssistantResponse
                      content={message.content}
                      timestamp={message.timestamp}
                    />
                  )}

                  {message.type === 'assistant' && index === messages.length - 1 && lastGroup && (
                    <div className="pl-11">
                      <ToolCallsAccumulator toolCalls={lastGroup.toolCalls} />
                    </div>
                  )}
                </div>
              );
            })}

            {isLoading && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-accent-muted flex items-center justify-center shrink-0">
                  <span className="text-body-xs font-semibold text-accent-text">AI</span>
                </div>
                <div className="bg-surface-elevated border border-line px-5 py-4 rounded-2xl rounded-tl-md">
                  <div className="flex items-center gap-2 text-content-tertiary">
                    <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <ChatInput onSubmit={handleSendMessage} disabled={isLoading} />
    </div>
  );
}