import { useState, useRef, useCallback, type KeyboardEvent } from 'react';
import { cn } from '@/lib/cn';
import { VoiceInputButton } from '@/components/voice/VoiceInputButton';

interface ChatInputProps {
  readonly onSend: (message: string) => void;
  readonly onCancel?: () => void;
  readonly isStreaming: boolean;
  readonly disabled?: boolean;
  readonly placeholder?: string;
  readonly voiceInputEnabled?: boolean;
}

export function ChatInput({
  onSend,
  onCancel,
  isStreaming,
  disabled = false,
  placeholder = 'Ask me anything about your practice...',
  voiceInputEnabled = false,
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const [interimText, setInterimText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    setInterimText('');
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

  const handleVoiceTranscript = useCallback((transcript: string, isFinal: boolean) => {
    if (isFinal) {
      setValue((prev) => prev + transcript);
      setInterimText('');
    } else {
      setInterimText(transcript);
    }
  }, []);

  const displayValue = value + (interimText ? ` ${interimText}` : '');
  const canSend = (value.trim().length > 0 || interimText.trim().length > 0) && !disabled && !isStreaming;
  const actionDisabled = isStreaming ? !onCancel : !canSend;

  return (
    <div className="relative">
      <div
        className={cn(
          'flex items-center gap-3 rounded-xl border bg-surface-elevated px-4 py-2.5',
          'transition-all duration-200',
          'focus-within:border-accent/40 focus-within:ring-1 focus-within:ring-accent/20',
          disabled ? 'opacity-60 pointer-events-none' : 'border-line',
        )}
      >
        {voiceInputEnabled && (
          <VoiceInputButton
            onTranscript={handleVoiceTranscript}
            disabled={disabled || isStreaming}
          />
        )}

        <textarea
          ref={textareaRef}
          value={displayValue}
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
            'min-h-[24px] max-h-[200px] leading-[24px]',
            interimText && 'italic text-content-secondary',
          )}
        />

        <button
          onClick={isStreaming ? onCancel : handleSend}
          disabled={actionDisabled}
          className={cn(
            'shrink-0 px-4 py-1.5 rounded-lg text-body-sm font-medium',
            'transition-colors duration-150',
            isStreaming
              ? 'text-status-error hover:bg-status-error/10'
              : canSend
                ? 'bg-accent text-surface-primary hover:bg-accent-hover'
                : 'text-content-tertiary',
          )}
        >
          {isStreaming ? 'Stop' : 'Send'}
        </button>
      </div>

      <p className="mt-1.5 text-center text-body-xs text-content-tertiary">
        Press <kbd className="px-1 py-0.5 rounded bg-surface-secondary text-body-xs font-mono">Enter</kbd> to send,{' '}
        <kbd className="px-1 py-0.5 rounded bg-surface-secondary text-body-xs font-mono">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
