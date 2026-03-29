import { motion, AnimatePresence } from 'framer-motion';
import { Plus, MessageCircle } from 'lucide-react';
import { Button } from '@/design-system/primitives/Button';
import type { AssistantSessionView } from '@/data/types';
import { cn } from '@/lib/cn';

interface SessionSidebarProps {
  readonly sessions: AssistantSessionView[];
  readonly activeSessionId: string | null;
  readonly onSelectSession: (sessionId: string) => void;
  readonly onNewSession: () => void;
  readonly isLoading: boolean;
}

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function getSessionPreview(session: AssistantSessionView): string {
  const lastMsg = session.messages[session.messages.length - 1];
  if (!lastMsg) return 'New conversation';
  const text = lastMsg.content;
  return text.length > 60 ? text.slice(0, 60) + '...' : text;
}

export function SessionSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  isLoading,
}: SessionSidebarProps) {
  return (
    <div className="flex flex-col h-full bg-surface-primary border-r border-line">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-line">
        <h2 className="font-display text-display-sm text-content-primary">Chats</h2>
        <Button
          variant="primary"
          size="sm"
          icon={<Plus className="w-4 h-4" />}
          onClick={onNewSession}
          disabled={isLoading}
        >
          New
        </Button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto py-2">
        {isLoading && sessions.length === 0 ? (
          <div className="flex flex-col gap-2 px-3">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="h-16 rounded-xl bg-surface-secondary animate-skeleton-pulse"
              />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <div className="w-10 h-10 rounded-full bg-surface-secondary flex items-center justify-center mb-3">
              <MessageCircle className="w-5 h-5 text-content-tertiary" />
            </div>
            <p className="text-body-sm text-content-secondary mb-1">No conversations yet</p>
            <p className="text-body-xs text-content-tertiary">Start a new chat to begin</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {sessions.map((session) => {
              const isActive = session.id === activeSessionId;
              return (
                <motion.button
                  key={session.id}
                  layout
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  onClick={() => onSelectSession(session.id)}
                  className={cn(
                    'w-full text-left px-3 py-2.5 mx-2 rounded-xl transition-all duration-150',
                    'hover:bg-surface-secondary/80 group',
                    isActive
                      ? 'bg-accent/[0.06] border border-accent/20'
                      : 'border border-transparent',
                  )}
                >
                  <div className="flex items-start gap-2.5">
                    <div
                      className={cn(
                        'shrink-0 w-8 h-8 rounded-lg flex items-center justify-center mt-0.5',
                        isActive ? 'bg-accent/10 text-accent' : 'bg-surface-secondary text-content-tertiary',
                      )}
                    >
                      <MessageCircle className="w-4 h-4" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <p
                        className={cn(
                          'text-body-sm font-medium truncate',
                          isActive ? 'text-accent' : 'text-content-primary',
                        )}
                      >
                        {session.title ?? 'Untitled Chat'}
                      </p>
                      <p className="text-body-xs text-content-tertiary truncate mt-0.5">
                        {getSessionPreview(session)}
                      </p>
                    </div>

                    <span className="text-body-xs text-content-tertiary shrink-0 mt-0.5">
                      {formatRelativeTime(session.updated_at)}
                    </span>
                  </div>
                </motion.button>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
