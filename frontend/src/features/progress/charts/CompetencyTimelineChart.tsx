import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/cn';
import type { ProgressHistorySnapshot } from '@/data';

interface CompetencyTimelineChartProps {
  readonly snapshots: ProgressHistorySnapshot[];
  readonly height?: number;
  readonly className?: string;
}

const CHART_PADDING = { top: 20, right: 20, bottom: 40, left: 50 };

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

const competencyColors = [
  'var(--color-status-success)',
  'var(--color-accent)',
  'var(--color-status-warning)',
  'var(--color-status-error)',
  '#8B5CF6',
  '#EC4899',
  '#14B8A6',
];

export function CompetencyTimelineChart({
  snapshots,
  height = 300,
  className,
}: CompetencyTimelineChartProps) {
  const chartDimensions = useMemo(() => {
    const width = 700;
    const innerWidth = width - CHART_PADDING.left - CHART_PADDING.right;
    const innerHeight = height - CHART_PADDING.top - CHART_PADDING.bottom;
    return { width, innerWidth, innerHeight };
  }, [height]);

  const { competencySlugs, seriesData } = useMemo(() => {
    if (snapshots.length === 0) return { competencySlugs: [], seriesData: [] };

    // Get unique competency slugs from first snapshot
    const slugs =
      snapshots[0]?.competency_states.map((c) => c.competency_slug) ?? [];

    // Build series data: for each competency, array of scores over time
    const series = slugs.map((slug) => {
      const data = snapshots.map((snap) => {
        const state = snap.competency_states.find(
          (c) => c.competency_slug === slug
        );
        return {
          score: state?.score ?? 0,
          confidence: state?.confidence ?? 0,
          recorded_at: snap.recorded_at,
        };
      });
      return { slug, data };
    });

    return { competencySlugs: slugs, seriesData: series };
  }, [snapshots]);

  const scales = useMemo(() => {
    if (snapshots.length === 0) return null;

    const xScale = (index: number) =>
      CHART_PADDING.left +
      (index / Math.max(1, snapshots.length - 1)) * chartDimensions.innerWidth;

    const yScale = (value: number) =>
      CHART_PADDING.top + (1 - value) * chartDimensions.innerHeight;

    return { xScale, yScale };
  }, [snapshots, chartDimensions]);

  const getPathData = (series: { score: number }[]) => {
    if (!scales) return '';
    return series
      .map((point, i) => {
        const x = scales.xScale(i);
        const y = scales.yScale(point.score);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  };

  const yAxisTicks = [0, 0.25, 0.5, 0.75, 1];

  if (snapshots.length === 0 || competencySlugs.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center justify-center h-64 text-content-tertiary',
          className
        )}
      >
        No competency timeline data available
      </div>
    );
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="mb-4">
        <h3 className="font-display text-display-xs text-content-primary">
          Competency Progress Over Time
        </h3>
        <p className="text-body-sm text-content-secondary">
          Track how your core competencies evolve
        </p>
      </div>

      <svg
        viewBox={`0 0 ${chartDimensions.width} ${height}`}
        className="w-full"
        style={{ height }}
      >
        {/* Grid lines */}
        {yAxisTicks.map((tick) => (
          <line
            key={tick}
            x1={CHART_PADDING.left}
            y1={scales!.yScale(tick)}
            x2={chartDimensions.width - CHART_PADDING.right}
            y2={scales!.yScale(tick)}
            stroke="var(--color-line)"
            strokeDasharray="4 4"
            strokeOpacity={0.5}
          />
        ))}

        {/* Y-axis labels */}
        {yAxisTicks.map((tick) => (
          <text
            key={tick}
            x={CHART_PADDING.left - 10}
            y={scales!.yScale(tick)}
            textAnchor="end"
            dominantBaseline="middle"
            className="text-body-xs fill-content-tertiary"
          >
            {Math.round(tick * 100)}%
          </text>
        ))}

        {/* X-axis labels */}
        {snapshots.map((snap, i) => (
          <text
            key={i}
            x={scales!.xScale(i)}
            y={height - 10}
            textAnchor="middle"
            className="text-body-xs fill-content-tertiary"
          >
            {formatDate(snap.recorded_at)}
          </text>
        ))}

        {/* Competency lines */}
        {seriesData.map((series, seriesIndex) => (
          <g key={series.slug}>
            <motion.path
              d={getPathData(series.data)}
              fill="none"
              stroke={competencyColors[seriesIndex % competencyColors.length]}
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1, ease: 'easeOut', delay: seriesIndex * 0.1 }}
            />
            {/* Data points */}
            {series.data.map((point, i) => (
              <motion.circle
                key={i}
                cx={scales!.xScale(i)}
                cy={scales!.yScale(point.score)}
                r={4}
                fill="var(--color-surface-elevated)"
                stroke={competencyColors[seriesIndex % competencyColors.length]}
                strokeWidth={2}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{
                  delay: 0.5 + seriesIndex * 0.1 + i * 0.03,
                  duration: 0.2,
                }}
              />
            ))}
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 mt-4">
        {seriesData.map((series, i) => (
          <div key={series.slug} className="flex items-center gap-1.5">
            <div
              className="w-4 h-1 rounded-full"
              style={{
                backgroundColor: competencyColors[i % competencyColors.length],
              }}
            />
            <span className="text-body-xs text-content-secondary">
              {series.slug
                .split('-')
                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(' ')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
