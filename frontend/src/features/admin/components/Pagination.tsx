import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/design-system/primitives/Button';
import { cn } from '@/lib/cn';

interface PaginationProps {
  readonly currentPage: number;
  readonly totalPages: number;
  readonly onPageChange: (page: number) => void;
  readonly className?: string;
}

export function Pagination({ currentPage, totalPages, onPageChange, className }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className={cn('flex items-center justify-between', className)}>
      <span className="text-body-xs text-content-tertiary">
        Page {currentPage} of {totalPages}
      </span>
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          icon={<ChevronLeft className="w-4 h-4" />}
        >
          Previous
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          icon={<ChevronRight className="w-4 h-4" />}
          iconPosition="right"
        >
          Next
        </Button>
      </div>
    </div>
  );
}
