import type { ReactNode } from 'react';
import { Card } from '@/design-system/primitives/Card';
import { cn } from '@/lib/cn';

export interface Column<T> {
  readonly key: string;
  readonly header: ReactNode;
  readonly width?: string;
  readonly render?: (item: T) => ReactNode;
}

interface DataTableProps<T> {
  readonly columns: Column<T>[];
  readonly data: T[];
  readonly keyExtractor: (item: T) => string;
  readonly onRowClick?: (item: T) => void;
  readonly emptyMessage?: string;
  readonly className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyMessage = 'No data available',
  className,
}: DataTableProps<T>) {
  if (data.length === 0) {
    return (
      <Card className={cn('flex items-center justify-center py-12', className)}>
        <p className="text-body-sm text-content-tertiary">{emptyMessage}</p>
      </Card>
    );
  }

  return (
    <Card padding="none" className={cn('overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-line bg-surface-secondary/50">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-left text-body-xs font-semibold text-content-secondary uppercase tracking-wider"
                  style={{ width: col.width }}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data.map((item) => (
              <tr
                key={keyExtractor(item)}
                onClick={() => onRowClick?.(item)}
                className={cn(
                  'transition-colors duration-150',
                  onRowClick && 'cursor-pointer hover:bg-surface-secondary/50',
                )}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-body-sm text-content-primary">
                    {col.render ? col.render(item) : String((item as Record<string, unknown>)[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
