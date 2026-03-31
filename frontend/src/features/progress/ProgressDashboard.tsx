import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, Activity, Target, Layers, Award } from 'lucide-react';
import { cn } from '@/lib/cn';
import { Card } from '@/design-system/primitives/Card';
import { useData } from '@/data';
import type {
  ProgressHistory,
  SkillTimeline,
} from '@/data';
import {
  SkillTimelineChart,
  CompetencyRadarChart,
  CompetencyTimelineChart,
  CompetencyProgressCard,
  ProgressHeatmap,
  SkillProgressCard,
  WeakSkillsTracker,
} from './charts';

interface ProgressDashboardProps {
  readonly className?: string;
}

type ViewMode = 'overview' | 'timeline' | 'competencies' | 'heatmap' | 'skills';

interface TabButtonProps {
  readonly active: boolean;
  readonly onClick: () => void;
  readonly icon: typeof BarChart3;
  readonly label: string;
}

function TabButton({ active, onClick, icon: Icon, label }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 px-4 py-2 rounded-lg text-body-sm font-medium transition-all',
        active
          ? 'bg-accent text-white'
          : 'bg-surface-secondary text-content-secondary hover:bg-surface-tertiary hover:text-content-primary'
      )}
    >
      <Icon size={16} />
      <span>{label}</span>
    </button>
  );
}

export function ProgressDashboard({ className }: ProgressDashboardProps) {
  const data = useData();
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [progressHistory, setProgressHistory] = useState<ProgressHistory | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [skillTimeline, setSkillTimeline] = useState<SkillTimeline | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    data.getProgressHistory({ limit: 20 }).then((history) => {
      setProgressHistory(history);
      setLoading(false);
    });
  }, [data]);

  useEffect(() => {
    if (selectedSkill) {
      data.getSkillTimeline(selectedSkill, { limit: 15 }).then(setSkillTimeline);
    }
  }, [selectedSkill, data]);

  const latestSnapshot = useMemo(() => {
    if (!progressHistory || progressHistory.snapshots.length === 0) return null;
    return progressHistory.snapshots[progressHistory.snapshots.length - 1];
  }, [progressHistory]);

  const overallStats = useMemo(() => {
    if (!latestSnapshot) return null;

    const avgScore =
      latestSnapshot.skill_states.reduce((sum, s) => sum + s.score, 0) /
      latestSnapshot.skill_states.length;

    const avgConfidence =
      latestSnapshot.skill_states.reduce((sum, s) => sum + s.confidence, 0) /
      latestSnapshot.skill_states.length;

    const totalEvidence = latestSnapshot.skill_states.reduce(
      (sum, s) => sum + s.evidence_count,
      0
    );

    const improvingCount = latestSnapshot.skill_states.filter((s) => s.delta > 0.02).length;

    return { avgScore, avgConfidence, totalEvidence, improvingCount };
  }, [latestSnapshot]);

  if (loading) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="h-12 bg-surface-secondary rounded-lg animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-surface-secondary rounded-lg animate-pulse" />
          ))}
        </div>
        <div className="h-80 bg-surface-secondary rounded-lg animate-pulse" />
      </div>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* View Mode Tabs */}
      <div className="flex flex-wrap gap-2">
        <TabButton
          active={viewMode === 'overview'}
          onClick={() => setViewMode('overview')}
          icon={Layers}
          label="Overview"
        />
        <TabButton
          active={viewMode === 'timeline'}
          onClick={() => setViewMode('timeline')}
          icon={Activity}
          label="Timeline"
        />
        <TabButton
          active={viewMode === 'competencies'}
          onClick={() => setViewMode('competencies')}
          icon={Award}
          label="Competencies"
        />
        <TabButton
          active={viewMode === 'heatmap'}
          onClick={() => setViewMode('heatmap')}
          icon={BarChart3}
          label="Heatmap"
        />
        <TabButton
          active={viewMode === 'skills'}
          onClick={() => setViewMode('skills')}
          icon={Target}
          label="Skills"
        />
      </div>

      {/* Stats Summary */}
      {overallStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0 }}
          >
            <Card className="text-center">
              <p className="text-body-xs text-content-tertiary mb-1">Average Score</p>
              <p className="text-display-md font-display font-bold text-content-primary">
                {Math.round(overallStats.avgScore * 100)}%
              </p>
            </Card>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="text-center">
              <p className="text-body-xs text-content-tertiary mb-1">Confidence</p>
              <p className="text-display-md font-display font-bold text-accent">
                {Math.round(overallStats.avgConfidence * 100)}%
              </p>
            </Card>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="text-center">
              <p className="text-body-xs text-content-tertiary mb-1">Total Evidence</p>
              <p className="text-display-md font-display font-bold text-content-primary">
                {overallStats.totalEvidence}
              </p>
            </Card>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="text-center">
              <p className="text-body-xs text-content-tertiary mb-1">Improving Skills</p>
              <p className="text-display-md font-display font-bold text-status-success">
                {overallStats.improvingCount}
              </p>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Main Content Area */}
      <AnimatePresence mode="popLayout">
        {viewMode === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Competency Radar */}
            {latestSnapshot && (
              <Card>
                <h3 className="font-display text-display-xs text-content-primary mb-4">
                  Competency Overview
                </h3>
                <CompetencyRadarChart
                  competencies={latestSnapshot.competency_states}
                  size={300}
                />
              </Card>
            )}

            {/* Weak Skills Tracker */}
            {latestSnapshot && (
              <WeakSkillsTracker
                weakSkills={latestSnapshot.weak_skill_slugs}
                stagnatingSkills={latestSnapshot.stagnating_skill_slugs}
                coverageGaps={latestSnapshot.coverage_gap_skill_slugs}
              />
            )}
          </motion.div>
        )}

        {viewMode === 'timeline' && (
          <motion.div
            key="timeline"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-6"
          >
            {/* Skill Selector */}
            <Card>
              <h3 className="font-display text-display-xs text-content-primary mb-4">
                Select a Skill to View Timeline
              </h3>
              <div className="flex flex-wrap gap-2">
                {latestSnapshot?.skill_states.map((skill) => (
                  <button
                    key={skill.skill_slug}
                    onClick={() => setSelectedSkill(skill.skill_slug)}
                    className={cn(
                      'px-3 py-1.5 rounded-full text-body-sm font-medium transition-all',
                      selectedSkill === skill.skill_slug
                        ? 'bg-accent text-white'
                        : 'bg-surface-secondary text-content-secondary hover:bg-surface-tertiary'
                    )}
                  >
                    {skill.skill_slug
                      .split('-')
                      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                      .join(' ')}
                  </button>
                ))}
              </div>
            </Card>

            {/* Timeline Chart */}
            {skillTimeline && (
              <Card>
                <SkillTimelineChart timeline={skillTimeline} height={320} />
              </Card>
            )}

            {!selectedSkill && (
              <Card className="text-center py-12">
                <Activity size={48} className="mx-auto text-content-tertiary mb-4" />
                <p className="text-content-secondary">
                  Select a skill above to view its progress timeline
                </p>
              </Card>
            )}
          </motion.div>
        )}

        {viewMode === 'heatmap' && progressHistory && (
          <motion.div
            key="heatmap"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            <Card>
              <ProgressHeatmap snapshots={progressHistory.snapshots} maxSkills={10} />
            </Card>
          </motion.div>
        )}

        {viewMode === 'competencies' && progressHistory && latestSnapshot && (
          <motion.div
            key="competencies"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-6"
          >
            {/* Competency Timeline */}
            <Card>
              <CompetencyTimelineChart
                snapshots={progressHistory.snapshots}
                height={320}
              />
            </Card>

            {/* Competency Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {latestSnapshot.competency_states.map((comp) => (
                <CompetencyProgressCard
                  key={comp.competency_slug}
                  competency={comp}
                />
              ))}
            </div>
          </motion.div>
        )}

        {viewMode === 'skills' && latestSnapshot && (
          <motion.div
            key="skills"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {latestSnapshot.skill_states.map((skill) => (
              <SkillProgressCard
                key={skill.skill_slug}
                skill={skill}
                onClick={() => {
                  setSelectedSkill(skill.skill_slug);
                  setViewMode('timeline');
                }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
