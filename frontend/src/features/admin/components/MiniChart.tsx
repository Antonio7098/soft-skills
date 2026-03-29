import { cn } from '@/lib/cn';

interface DataPoint {
  readonly label: string;
  readonly value: number;
}

interface MiniChartProps {
  readonly data: DataPoint[];
  readonly height?: number;
  readonly color?: 'accent' | 'success' | 'error' | 'warning';
  readonly className?: string;
}

const colorMap = {
  accent: 'bg-accent',
  success: 'bg-status-success',
  error: 'bg-status-error',
  warning: 'bg-status-warning',
};

export function MiniChart({ data, height = 48, color = 'accent', className }: MiniChartProps) {
  if (data.length === 0) return null;

  const maxValue = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className={cn('flex items-end gap-1', className)} style={{ height }}>
      {data.map((point, idx) => {
        const barHeight = (point.value / maxValue) * 100;
        return (
          <div
            key={idx}
            className="flex-1 flex flex-col items-center gap-1"
          >
            <div
              className={cn('w-full rounded-sm transition-all duration-300', colorMap[color])}
              style={{ height: `${Math.max(barHeight, 4)}%`, opacity: 0.7 + (barHeight / 100) * 0.3 }}
              title={`${point.label}: ${point.value}`}
            />
          </div>
        );
      })}
    </div>
  );
}

interface SparklineProps {
  readonly data: number[];
  readonly width?: number;
  readonly height?: number;
  readonly color?: 'accent' | 'success' | 'error';
  readonly className?: string;
}

export function Sparkline({ data, width = 80, height = 24, color = 'accent', className }: SparklineProps) {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((value, idx) => {
    const x = (idx / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  const strokeColor = color === 'accent' 
    ? 'var(--color-accent)' 
    : color === 'success' 
      ? 'var(--color-status-success)' 
      : 'var(--color-status-error)';

  return (
    <svg width={width} height={height} className={className}>
      <polyline
        points={points}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
