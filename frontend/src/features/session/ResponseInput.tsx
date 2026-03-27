import { useState } from 'react';
import { Send } from 'lucide-react';
import { Textarea } from '@/design-system/primitives/Textarea';
import { Button } from '@/design-system/primitives/Button';
import { cn } from '@/lib/cn';

interface ResponseInputProps {
  readonly onSubmit: (text: string) => void;
  readonly loading?: boolean;
  readonly placeholder?: string;
  readonly submitLabel?: string;
  readonly minLength?: number;
  readonly className?: string;
}

export function ResponseInput({
  onSubmit,
  loading = false,
  placeholder = 'Type your response here...',
  submitLabel = 'Submit Response',
  minLength = 20,
  className,
}: ResponseInputProps) {
  const [text, setText] = useState('');

  function handleSubmit() {
    if (text.trim().length >= minLength) {
      onSubmit(text.trim());
      setText('');
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit();
    }
  }

  const charCount = text.trim().length;
  const isValid = charCount >= minLength;

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={loading}
        className="min-h-[160px]"
      />
      <div className="flex items-center justify-between">
        <span className={cn(
          'text-body-xs transition-colors',
          isValid ? 'text-content-tertiary' : 'text-status-warning',
        )}>
          {charCount} characters {!isValid && `(min ${minLength})`}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-body-xs text-content-tertiary hidden sm:inline">⌘+Enter to submit</span>
          <Button
            variant="primary"
            size="md"
            icon={<Send className="w-4 h-4" />}
            iconPosition="right"
            loading={loading}
            disabled={!isValid || loading}
            onClick={handleSubmit}
          >
            {submitLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
