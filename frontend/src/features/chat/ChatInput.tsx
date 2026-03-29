import { useState, useRef, useCallback, type KeyboardEvent } from 'react';
import { Send, Square } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ChatInputProps {
  readonly onSend: (message: string) => void;
  readonly onCancel?: () => void;
  readonly isStreaming: boolean;
  readonly disabled?: boolean;
  readonly placeholder?: string;
}

export function ChatInput({
  onSend,
  onCancel,
  isStreaming,
  disabled = false,
  placeholder = 'Ask me anything about your practice...',
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (isStreaming) return;
        handleSend();
      }
    },
    [handleSend, isStreaming],
  );

  const handleInput = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  const canSend = value.trim().length > 0 && !disabled && !isStreaming;
  const actionDisabled = isStreaming ? !onCancel : !canSend;

  return (
    <div className="relative">
      <div
        className={cn(
          'flex items-end gap-2 rounded-2xl border bg-surface-elevated px-4 py-3',
          'shadow-card transition-all duration-200',
          'focus-within:border-accent/40 focus-within:shadow-elevated',
          disabled ? 'opacity-60 pointer-events-none' : 'border-line',
        )}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={placeholder}
          disabled={disabled || isStreaming}
          rows={1}
          className={cn(
            'flex-1 resize-none bg-transparent text-body-md text-content-primary',
            'placeholder:text-content-tertiary',
            'focus:outline-none',
            'min-h-[24px] max-h-[200px]',
          )}
        />

        <button
          onClick={isStreaming ? onCancel : handleSend}
          disabled={actionDisabled}
          className={cn(
            'shrink-0 w-9 h-9 rounded-xl flex items-center justify-center',
            'transition-colors duration-150',
            isStreaming
              ? 'bg-status-error/10 text-status-error hover:bg-status-error/20'
              : canSend
                ? 'bg-accent text-surface-primary hover:bg-accent-hover shadow-sm'
                : 'bg-surface-secondary text-content-tertiary',
          )}
          aria-label={isStreaming ? 'Cancel generation' : 'Send message'}
        >
          {isStreaming ? (
            <Square className="w-4 h-4 fill-current" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>

      <p className="mt-1.5 text-center text-body-xs text-content-tertiary">
        Press <kbd className="px-1 py-0.5 rounded bg-surface-secondary text-body-xs font-mono">Enter</kbd> to send,{' '}
        <kbd className="px-1 py-0.5 rounded bg-surface-secondary text-body-xs font-mono">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
