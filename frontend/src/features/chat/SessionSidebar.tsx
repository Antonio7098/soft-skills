import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, History, X } from 'lucide-react';
import type { AssistantSessionView } from '@/data/types';
import { cn } from '@/lib/cn';

interface SessionModalProps {
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

export function SessionModal({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  isLoading,
}: SessionModalProps) {
  const [open, setOpen] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close on click outside
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (
        modalRef.current &&
        !modalRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open]);

  const handleSelect = (sessionId: string) => {
    onSelectSession(sessionId);
    setOpen(false);
  };

  const handleNew = () => {
    onNewSession();
    setOpen(false);
  };

  return (
    <div className="relative">
      {/* Trigger button */}
      <button
        ref={buttonRef}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg text-body-sm font-medium',
          'transition-colors duration-150',
          open
            ? 'bg-accent/10 text-accent'
            : 'text-content-secondary hover:text-content-primary hover:bg-surface-secondary',
        )}
      >
        <History className="w-4 h-4" />
        Sessions
      </button>

      {/* Modal popover */}
      <AnimatePresence>
        {open && (
          <motion.div
            ref={modalRef}
            initial={{ opacity: 0, y: -4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.97 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className={cn(
              'absolute top-full left-0 mt-2 z-50',
              'w-80 max-h-[420px] flex flex-col',
              'bg-surface-elevated border border-line rounded-xl shadow-elevated overflow-hidden',
            )}
          >
            {/* Modal header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-line">
              <p className="text-body-sm font-semibold text-content-primary">Previous Sessions</p>
              <div className="flex items-center gap-1">
                <button
                  onClick={handleNew}
                  disabled={isLoading}
                  className="flex items-center gap-1 px-2 py-1 rounded-md text-body-xs font-medium text-accent hover:bg-accent/10 transition-colors disabled:opacity-50"
                >
                  <Plus className="w-3.5 h-3.5" />
                  New
                </button>
                <button
                  onClick={() => setOpen(false)}
                  className="p-1 rounded-md text-content-tertiary hover:text-content-primary hover:bg-surface-secondary transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Session list */}
            <div className="flex-1 overflow-y-auto py-1">
              {isLoading && sessions.length === 0 ? (
                <div className="flex flex-col gap-1.5 px-2 py-2">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-12 rounded-lg bg-surface-secondary animate-skeleton-pulse"
                    />
                  ))}
                </div>
              ) : sessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
                  <p className="text-body-sm text-content-secondary mb-0.5">No sessions yet</p>
                  <p className="text-body-xs text-content-tertiary">Start a new chat to begin</p>
                </div>
              ) : (
                sessions.map((session) => {
                  const isActive = session.id === activeSessionId;
                  return (
                    <button
                      key={session.id}
                      onClick={() => handleSelect(session.id)}
                      className={cn(
                        'w-full text-left px-3 py-2.5 mx-1 rounded-lg transition-colors duration-100',
                        'hover:bg-surface-secondary',
                        isActive && 'bg-accent/[0.06]',
                      )}
                      style={{ width: 'calc(100% - 8px)' }}
                    >
                      <div className="flex items-baseline justify-between gap-2">
                        <p
                          className={cn(
                            'text-body-sm font-medium truncate',
                            isActive ? 'text-accent' : 'text-content-primary',
                          )}
                        >
                          {session.title ?? 'Untitled Chat'}
                        </p>
                        <span className="text-body-xs text-content-tertiary shrink-0">
                          {formatRelativeTime(session.updated_at)}
                        </span>
                      </div>
                      <p className="text-body-xs text-content-tertiary truncate mt-0.5">
                        {getSessionPreview(session)}
                      </p>
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
