import { Search } from 'lucide-react';
import { cn } from '@/lib/cn';

interface SearchInputProps {
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly placeholder?: string;
  readonly className?: string;
}

export function SearchInput({ value, onChange, placeholder = 'Search...', className }: SearchInputProps) {
  return (
    <div className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-content-tertiary" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={cn(
          'w-full h-9 pl-9 pr-3 rounded-lg',
          'bg-surface-secondary/50 border border-line',
          'text-body-sm text-content-primary placeholder:text-content-tertiary',
          'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/50',
          'transition-all duration-150',
        )}
      />
    </div>
  );
}
