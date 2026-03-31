import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/cn';
import type { SkillTimeline } from '@/data';

interface SkillTimelineChartProps {
  readonly timeline: SkillTimeline;
  readonly height?: number;
  readonly showConfidence?: boolean;
  readonly className?: string;
}

const CHART_PADDING = { top: 20, right: 20, bottom: 40, left: 50 };

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getTrendColor(trend: 'improving' | 'declining' | 'stable'): string {
  switch (trend) {
    case 'improving':
      return 'var(--color-status-success)';
    case 'declining':
      return 'var(--color-status-error)';
    default:
      return 'var(--color-accent)';
  }
}

export function SkillTimelineChart({
  timeline,
  height = 280,
  showConfidence = true,
  className,
}: SkillTimelineChartProps) {
  const { points, skill_name, trend, overall_change } = timeline;

  const chartDimensions = useMemo(() => {
    const width = 600;
    const innerWidth = width - CHART_PADDING.left - CHART_PADDING.right;
    const innerHeight = height - CHART_PADDING.top - CHART_PADDING.bottom;
    return { width, innerWidth, innerHeight };
  }, [height]);

  const scales = useMemo(() => {
    if (points.length === 0) return null;

    const xScale = (index: number) =>
      CHART_PADDING.left + (index / Math.max(1, points.length - 1)) * chartDimensions.innerWidth;

    const yScale = (value: number) =>
      CHART_PADDING.top + (1 - value) * chartDimensions.innerHeight;

    return { xScale, yScale };
  }, [points, chartDimensions]);

  const pathData = useMemo(() => {
    if (!scales || points.length === 0) return '';

    return points
      .map((point, i) => {
        const x = scales.xScale(i);
        const y = scales.yScale(point.score);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  }, [points, scales]);

  const confidenceAreaPath = useMemo(() => {
    if (!scales || points.length === 0 || !showConfidence) return '';

    const upperPath = points
      .map((point, i) => {
        const x = scales.xScale(i);
        const y = scales.yScale(Math.min(1, point.score + (1 - point.confidence) * 0.15));
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');

    const lowerPath = points
      .slice()
      .reverse()
      .map((point, i) => {
        const x = scales.xScale(points.length - 1 - i);
        const y = scales.yScale(Math.max(0, point.score - (1 - point.confidence) * 0.15));
        return `L ${x} ${y}`;
      })
      .join(' ');

    return `${upperPath} ${lowerPath} Z`;
  }, [points, scales, showConfidence]);

  const yAxisTicks = [0, 0.25, 0.5, 0.75, 1];
  const xAxisTicks = useMemo(() => {
    if (points.length <= 5) return points.map((_, i) => i);
    const step = Math.ceil(points.length / 5);
    return points.map((_, i) => i).filter((i) => i % step === 0 || i === points.length - 1);
  }, [points]);

  if (points.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-64 text-content-tertiary', className)}>
        No timeline data available
      </div>
    );
  }

  const trendColor = getTrendColor(trend);

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-display text-display-xs text-content-primary">{skill_name}</h3>
          <p className="text-body-sm text-content-secondary">Progress over time</p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="text-body-sm font-medium"
            style={{ color: trendColor }}
          >
            {overall_change >= 0 ? '+' : ''}
            {Math.round(overall_change * 100)}%
          </span>
          <span
            className="px-2 py-0.5 rounded-full text-body-xs font-medium capitalize"
            style={{
              backgroundColor: `color-mix(in srgb, ${trendColor} 15%, transparent)`,
              color: trendColor,
            }}
          >
            {trend}
          </span>
        </div>
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
        {xAxisTicks.map((i) => (
          <text
            key={i}
            x={scales!.xScale(i)}
            y={height - 10}
            textAnchor="middle"
            className="text-body-xs fill-content-tertiary"
          >
            {formatDate(points[i]!.recorded_at)}
          </text>
        ))}

        {/* Confidence band */}
        {showConfidence && (
          <motion.path
            d={confidenceAreaPath}
            fill="var(--color-accent)"
            fillOpacity={0.1}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          />
        )}

        {/* Main line */}
        <motion.path
          d={pathData}
          fill="none"
          stroke={trendColor}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />

        {/* Data points */}
        {points.map((point, i) => (
          <motion.g key={i}>
            <motion.circle
              cx={scales!.xScale(i)}
              cy={scales!.yScale(point.score)}
              r={5}
              fill="var(--color-surface-elevated)"
              stroke={trendColor}
              strokeWidth={2}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.5 + i * 0.05, duration: 0.2 }}
            />
            <title>
              {formatDate(point.recorded_at)}: {Math.round(point.score * 100)}% (Confidence:{' '}
              {Math.round(point.confidence * 100)}%)
            </title>
          </motion.g>
        ))}
      </svg>

      {/* Legend */}
      {showConfidence && (
        <div className="flex items-center gap-4 mt-3 text-body-xs text-content-tertiary">
          <div className="flex items-center gap-1.5">
            <div
              className="w-3 h-0.5 rounded-full"
              style={{ backgroundColor: trendColor }}
            />
            <span>Score</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-sm opacity-20"
              style={{ backgroundColor: 'var(--color-accent)' }}
            />
            <span>Confidence band</span>
          </div>
        </div>
      )}
    </div>
  );
}
