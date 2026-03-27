import { Input } from '@/design-system/primitives/Input';
import { Badge } from '@/design-system/primitives/Badge';
import { Search } from 'lucide-react';
import { cn } from '@/lib/cn';

type PracticeTypeFilter = 'all' | 'quick_practice' | 'interview' | 'scenario';

interface HistoryFiltersProps {
  readonly search: string;
  readonly onSearchChange: (value: string) => void;
  readonly practiceType: PracticeTypeFilter;
  readonly onPracticeTypeChange: (value: PracticeTypeFilter) => void;
  readonly className?: string;
}

const TYPE_OPTIONS: { value: PracticeTypeFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'quick_practice', label: 'Quick Practice' },
  { value: 'interview', label: 'Interview' },
  { value: 'scenario', label: 'Scenario' },
];

export function HistoryFilters({
  search,
  onSearchChange,
  practiceType,
  onPracticeTypeChange,
  className,
}: HistoryFiltersProps) {
  return (
    <div className={cn('flex flex-col sm:flex-row items-start sm:items-center gap-4', className)}>
      <div className="w-full sm:w-64">
        <Input
          placeholder="Search attempts..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          icon={<Search className="w-4 h-4" />}
        />
      </div>
      <div className="flex items-center gap-2">
        {TYPE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onPracticeTypeChange(opt.value)}
            className="focus:outline-none"
          >
            <Badge
              variant={practiceType === opt.value ? 'accent' : 'default'}
              size="md"
              className={cn(
                'cursor-pointer transition-all',
                practiceType === opt.value && 'ring-1 ring-accent/30',
              )}
            >
              {opt.label}
            </Badge>
          </button>
        ))}
      </div>
    </div>
  );
}

export type { PracticeTypeFilter };
