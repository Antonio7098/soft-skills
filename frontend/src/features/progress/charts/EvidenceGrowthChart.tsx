import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/cn';
import type { SkillTimelinePoint } from '@/data';

interface EvidenceGrowthChartProps {
  readonly points: SkillTimelinePoint[];
  readonly skillName: string;
  readonly height?: number;
  readonly className?: string;
}

const CHART_PADDING = { top: 20, right: 20, bottom: 40, left: 50 };

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function EvidenceGrowthChart({
  points,
  skillName,
  height = 200,
  className,
}: EvidenceGrowthChartProps) {
  const chartDimensions = useMemo(() => {
    const width = 500;
    const innerWidth = width - CHART_PADDING.left - CHART_PADDING.right;
    const innerHeight = height - CHART_PADDING.top - CHART_PADDING.bottom;
    return { width, innerWidth, innerHeight };
  }, [height]);

  const { maxEvidence, scales, barWidth } = useMemo(() => {
    if (points.length === 0) return { maxEvidence: 0, scales: null, barWidth: 0 };

    const max = Math.max(...points.map((p) => p.evidence_count));
    const barW = Math.min(40, chartDimensions.innerWidth / points.length - 4);

    const xScale = (index: number) =>
      CHART_PADDING.left +
      (index / points.length) * chartDimensions.innerWidth +
      barW / 2;

    const yScale = (value: number) =>
      CHART_PADDING.top + (1 - value / max) * chartDimensions.innerHeight;

    return { maxEvidence: max, scales: { xScale, yScale }, barWidth: barW };
  }, [points, chartDimensions]);

  if (points.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-48 text-content-tertiary', className)}>
        No evidence data available
      </div>
    );
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="mb-4">
        <h3 className="font-display text-display-xs text-content-primary">Evidence Growth</h3>
        <p className="text-body-sm text-content-secondary">{skillName} - Evidence accumulation over time</p>
      </div>

      <svg
        viewBox={`0 0 ${chartDimensions.width} ${height}`}
        className="w-full"
        style={{ height }}
      >
        {/* Y-axis grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
          <line
            key={tick}
            x1={CHART_PADDING.left}
            y1={scales!.yScale(tick * maxEvidence)}
            x2={chartDimensions.width - CHART_PADDING.right}
            y2={scales!.yScale(tick * maxEvidence)}
            stroke="var(--color-line)"
            strokeDasharray="4 4"
            strokeOpacity={0.3}
          />
        ))}

        {/* Y-axis labels */}
        {[0, 0.5, 1].map((tick) => (
          <text
            key={tick}
            x={CHART_PADDING.left - 10}
            y={scales!.yScale(tick * maxEvidence)}
            textAnchor="end"
            dominantBaseline="middle"
            className="text-body-xs fill-content-tertiary"
          >
            {Math.round(tick * maxEvidence)}
          </text>
        ))}

        {/* Bars */}
        {points.map((point, i) => {
          const barHeight =
            (point.evidence_count / maxEvidence) * chartDimensions.innerHeight;
          const x = scales!.xScale(i) - barWidth / 2;
          const y = CHART_PADDING.top + chartDimensions.innerHeight - barHeight;

          return (
            <motion.g key={i}>
              <motion.rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                rx={4}
                fill="var(--color-accent)"
                fillOpacity={0.7 + (i / points.length) * 0.3}
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{ delay: i * 0.05, duration: 0.3 }}
                style={{ transformOrigin: `${x + barWidth / 2}px ${CHART_PADDING.top + chartDimensions.innerHeight}px` }}
              />
              <text
                x={scales!.xScale(i)}
                y={y - 8}
                textAnchor="middle"
                className="text-body-xs fill-content-secondary font-medium"
              >
                {point.evidence_count}
              </text>
              <title>
                {formatDate(point.recorded_at)}: {point.evidence_count} evidence
              </title>
            </motion.g>
          );
        })}

        {/* X-axis labels */}
        {points.map((point, i) => (
          <text
            key={i}
            x={scales!.xScale(i)}
            y={height - 10}
            textAnchor="middle"
            className="text-body-xs fill-content-tertiary"
          >
            {formatDate(point.recorded_at)}
          </text>
        ))}
      </svg>
    </div>
  );
}
