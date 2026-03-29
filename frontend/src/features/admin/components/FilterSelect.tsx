import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/cn';

interface FilterOption {
  readonly value: string;
  readonly label: string;
}

interface FilterSelectProps {
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly options: FilterOption[];
  readonly placeholder?: string;
  readonly className?: string;
}

export function FilterSelect({ value, onChange, options, placeholder = 'Select...', className }: FilterSelectProps) {
  return (
    <div className={cn('relative', className)}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          'appearance-none w-full h-9 pl-3 pr-8 rounded-lg',
          'bg-surface-secondary/50 border border-line',
          'text-body-sm text-content-primary',
          'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/50',
          'transition-all duration-150 cursor-pointer',
        )}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-content-tertiary pointer-events-none" />
    </div>
  );
}
