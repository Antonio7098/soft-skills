import { useState, type FormEvent } from 'react';
import { Send } from 'lucide-react';
import { cn } from '@/lib/cn';
import { Button } from '@/design-system/primitives/Button';

interface ChatInputProps {
  readonly onSubmit: (message: string) => void;
  readonly placeholder?: string;
  readonly disabled?: boolean;
  readonly className?: string;
}

export function ChatInput({
  onSubmit,
  placeholder = 'Type a message...',
  disabled = false,
  className,
}: ChatInputProps) {
  const [value, setValue] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (value.trim() && !disabled) {
      onSubmit(value.trim());
      setValue('');
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        'flex items-end gap-3 p-4 bg-surface-elevated border-t border-line',
        className,
      )}
    >
      <div className="flex-1 relative">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={cn(
            'w-full px-4 py-3 pr-12 rounded-xl font-body text-body-sm',
            'bg-surface-secondary text-content-primary',
            'border border-line placeholder:text-content-tertiary',
            'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent',
            'transition-all duration-150 resize-none',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'max-h-[120px] overflow-y-auto',
          )}
          style={{ minHeight: '48px' }}
        />
      </div>
      <Button
        type="submit"
        variant="primary"
        size="md"
        icon={<Send className="w-4 h-4" />}
        disabled={!value.trim() || disabled}
        className="shrink-0 h-[48px] w-[48px] px-0"
      >
        <span className="sr-only">Send</span>
      </Button>
    </form>
  );
}