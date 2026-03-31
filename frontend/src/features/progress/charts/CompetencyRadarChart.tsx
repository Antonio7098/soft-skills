import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/cn';
import type { CompetencyHistoryPoint } from '@/data';

interface CompetencyRadarChartProps {
  readonly competencies: CompetencyHistoryPoint[];
  readonly size?: number;
  readonly className?: string;
}

function polarToCartesian(
  centerX: number,
  centerY: number,
  radius: number,
  angleInDegrees: number
): { x: number; y: number } {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180;
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  };
}

function getConfidenceColor(band: 'low' | 'medium' | 'high'): string {
  switch (band) {
    case 'high':
      return 'var(--color-status-success)';
    case 'medium':
      return 'var(--color-accent)';
    default:
      return 'var(--color-status-warning)';
  }
}

export function CompetencyRadarChart({
  competencies,
  size = 320,
  className,
}: CompetencyRadarChartProps) {
  const center = size / 2;
  const maxRadius = (size - 80) / 2;
  const levels = [0.25, 0.5, 0.75, 1];

  const points = useMemo(() => {
    if (competencies.length === 0) return [];

    const angleStep = 360 / competencies.length;
    return competencies.map((comp, i) => {
      const angle = i * angleStep;
      const radius = comp.score * maxRadius;
      const pos = polarToCartesian(center, center, radius, angle);
      const labelPos = polarToCartesian(center, center, maxRadius + 25, angle);
      return {
        ...comp,
        x: pos.x,
        y: pos.y,
        labelX: labelPos.x,
        labelY: labelPos.y,
        angle,
      };
    });
  }, [competencies, center, maxRadius]);

  const polygonPath = useMemo(() => {
    if (points.length === 0) return '';
    return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';
  }, [points]);

  if (competencies.length === 0) {
    return (
      <div className={cn('flex items-center justify-center text-content-tertiary', className)} style={{ height: size }}>
        No competency data available
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background circles */}
        {levels.map((level) => (
          <circle
            key={level}
            cx={center}
            cy={center}
            r={level * maxRadius}
            fill="none"
            stroke="var(--color-line)"
            strokeOpacity={0.3}
            strokeDasharray={level === 1 ? 'none' : '4 4'}
          />
        ))}

        {/* Axis lines */}
        {points.map((point, i) => (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={polarToCartesian(center, center, maxRadius, point.angle).x}
            y2={polarToCartesian(center, center, maxRadius, point.angle).y}
            stroke="var(--color-line)"
            strokeOpacity={0.3}
          />
        ))}

        {/* Data polygon fill */}
        <motion.path
          d={polygonPath}
          fill="var(--color-accent)"
          fillOpacity={0.15}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          style={{ transformOrigin: `${center}px ${center}px` }}
        />

        {/* Data polygon stroke */}
        <motion.path
          d={polygonPath}
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth={2}
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />

        {/* Data points */}
        {points.map((point, i) => (
          <motion.g key={i}>
            <motion.circle
              cx={point.x}
              cy={point.y}
              r={6}
              fill="var(--color-surface-elevated)"
              stroke={getConfidenceColor(point.confidence_band)}
              strokeWidth={2.5}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3 + i * 0.1, duration: 0.2 }}
            />
            <title>
              {point.competency_slug}: {Math.round(point.score * 100)}% (
              {point.confidence_band} confidence)
            </title>
          </motion.g>
        ))}

        {/* Labels */}
        {points.map((point, i) => (
          <text
            key={i}
            x={point.labelX}
            y={point.labelY}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-body-xs fill-content-secondary font-medium"
          >
            {point.competency_slug
              .split('-')
              .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
              .join(' ')
              .slice(0, 15)}
          </text>
        ))}

        {/* Level labels */}
        {levels.map((level) => (
          <text
            key={level}
            x={center + 5}
            y={center - level * maxRadius + 4}
            className="text-body-xs fill-content-tertiary"
          >
            {Math.round(level * 100)}%
          </text>
        ))}
      </svg>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-2 text-body-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full border-2" style={{ borderColor: 'var(--color-status-success)' }} />
          <span className="text-content-tertiary">High confidence</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full border-2" style={{ borderColor: 'var(--color-accent)' }} />
          <span className="text-content-tertiary">Medium</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full border-2" style={{ borderColor: 'var(--color-status-warning)' }} />
          <span className="text-content-tertiary">Low</span>
        </div>
      </div>
    </div>
  );
}
