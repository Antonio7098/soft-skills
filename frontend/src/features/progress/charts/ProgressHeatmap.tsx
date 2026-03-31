import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/cn';
import type { ProgressHistorySnapshot } from '@/data';

interface ProgressHeatmapProps {
  readonly snapshots: ProgressHistorySnapshot[];
  readonly maxSkills?: number;
  readonly className?: string;
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getScoreColor(score: number): string {
  if (score >= 0.8) return 'var(--color-status-success)';
  if (score >= 0.6) return 'var(--color-accent)';
  if (score >= 0.4) return 'var(--color-status-warning)';
  return 'var(--color-status-error)';
}

function getScoreOpacity(score: number): number {
  return 0.3 + score * 0.7;
}

export function ProgressHeatmap({
  snapshots,
  maxSkills = 8,
  className,
}: ProgressHeatmapProps) {
  const { skillSlugs, gridData, dateLabels } = useMemo(() => {
    if (snapshots.length === 0) return { skillSlugs: [], gridData: [], dateLabels: [] };

    // Get unique skill slugs from all snapshots
    const allSlugs = new Set<string>();
    snapshots.forEach((snap) => {
      snap.skill_states.forEach((s) => allSlugs.add(s.skill_slug));
    });
    const slugs = Array.from(allSlugs).slice(0, maxSkills);

    // Build grid data: rows = skills, cols = snapshots
    const grid = slugs.map((slug) => {
      return snapshots.map((snap) => {
        const skillState = snap.skill_states.find((s) => s.skill_slug === slug);
        return {
          score: skillState?.score ?? 0,
          confidence: skillState?.confidence ?? 0,
          delta: skillState?.delta ?? 0,
        };
      });
    });

    const dates = snapshots.map((s) => formatDate(s.recorded_at));

    return { skillSlugs: slugs, gridData: grid, dateLabels: dates };
  }, [snapshots, maxSkills]);

  const cellSize = 36;
  const labelWidth = 140;
  const headerHeight = 50;
  const chartWidth = labelWidth + snapshots.length * cellSize + 20;
  const chartHeight = headerHeight + skillSlugs.length * cellSize + 20;

  if (snapshots.length === 0 || skillSlugs.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-48 text-content-tertiary', className)}>
        No progress data available
      </div>
    );
  }

  return (
    <div className={cn('w-full overflow-x-auto', className)}>
      <div className="mb-4">
        <h3 className="font-display text-display-xs text-content-primary">Skill Progress Heatmap</h3>
        <p className="text-body-sm text-content-secondary">Score intensity over time</p>
      </div>

      <svg width={chartWidth} height={chartHeight} className="min-w-full">
        {/* Date headers */}
        {dateLabels.map((date, i) => (
          <text
            key={i}
            x={labelWidth + i * cellSize + cellSize / 2}
            y={headerHeight - 10}
            textAnchor="middle"
            className="text-body-xs fill-content-tertiary"
            transform={`rotate(-45, ${labelWidth + i * cellSize + cellSize / 2}, ${headerHeight - 10})`}
          >
            {date}
          </text>
        ))}

        {/* Skill labels and cells */}
        {skillSlugs.map((slug, rowIndex) => (
          <g key={slug}>
            {/* Skill label */}
            <text
              x={labelWidth - 10}
              y={headerHeight + rowIndex * cellSize + cellSize / 2}
              textAnchor="end"
              dominantBaseline="middle"
              className="text-body-xs fill-content-secondary font-medium"
            >
              {slug
                .split('-')
                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(' ')
                .slice(0, 18)}
            </text>

            {/* Cells */}
            {gridData[rowIndex]?.map((cell, colIndex) => (
              <motion.g key={colIndex}>
                <motion.rect
                  x={labelWidth + colIndex * cellSize + 2}
                  y={headerHeight + rowIndex * cellSize + 2}
                  width={cellSize - 4}
                  height={cellSize - 4}
                  rx={4}
                  fill={getScoreColor(cell.score)}
                  fillOpacity={getScoreOpacity(cell.score)}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{
                    delay: (rowIndex * snapshots.length + colIndex) * 0.01,
                    duration: 0.2,
                  }}
                  style={{ transformOrigin: 'center' }}
                />
                <title>
                  {slug}: {Math.round(cell.score * 100)}%
                  {cell.delta !== 0 && ` (${cell.delta >= 0 ? '+' : ''}${Math.round(cell.delta * 100)}%)`}
                </title>
              </motion.g>
            ))}
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="flex items-center gap-6 mt-4 text-body-xs text-content-tertiary">
        <span>Score:</span>
        <div className="flex items-center gap-1">
          {[0.2, 0.4, 0.6, 0.8, 1].map((score) => (
            <div
              key={score}
              className="w-5 h-5 rounded"
              style={{
                backgroundColor: getScoreColor(score),
                opacity: getScoreOpacity(score),
              }}
              title={`${Math.round(score * 100)}%`}
            />
          ))}
        </div>
        <span className="ml-2">Low → High</span>
      </div>
    </div>
  );
}
