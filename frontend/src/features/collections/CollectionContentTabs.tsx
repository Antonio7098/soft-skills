import { useState } from 'react';
import { Brain, Briefcase, Target, LayoutGrid } from 'lucide-react';
import { motion } from 'framer-motion';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { PromptItemCard } from './PromptItemCard';
import { ScenarioOverviewCard } from './ScenarioOverviewCard';
import type { CollectionView } from '@/data';
import { cn } from '@/lib/cn';

interface CollectionContentTabsProps {
  readonly collection: CollectionView;
}

type TabId = 'all' | 'quick' | 'interview' | 'scenario';

interface TabDef {
  readonly id: TabId;
  readonly label: string;
  readonly icon: React.ComponentType<{ className?: string }>;
  readonly count: number;
}

export function CollectionContentTabs({ collection }: CollectionContentTabsProps) {
  const quickItems = collection.prompt_items.filter((p) => p.prompt_type === 'quick_practice_prompt');
  const interviewItems = collection.prompt_items.filter((p) => p.prompt_type === 'interview_prompt');
  const scenarios = collection.scenarios;

  const tabs: TabDef[] = [
    { id: 'all', label: 'All Items', icon: LayoutGrid, count: collection.prompt_items.length + scenarios.length },
    { id: 'quick', label: 'Quick Practice', icon: Brain, count: quickItems.length },
    { id: 'interview', label: 'Interview', icon: Briefcase, count: interviewItems.length },
    { id: 'scenario', label: 'Scenarios', icon: Target, count: scenarios.length },
  ];

  const [activeTab, setActiveTab] = useState<TabId>('all');

  const showQuick = activeTab === 'all' || activeTab === 'quick';
  const showInterview = activeTab === 'all' || activeTab === 'interview';
  const showScenario = activeTab === 'all' || activeTab === 'scenario';

  const hasContent = (showQuick && quickItems.length > 0) ||
    (showInterview && interviewItems.length > 0) ||
    (showScenario && scenarios.length > 0);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2 border-b border-line pb-px overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 text-body-sm font-medium rounded-t-lg transition-all relative whitespace-nowrap',
                isActive
                  ? 'text-accent'
                  : 'text-content-tertiary hover:text-content-secondary',
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              <span className={cn(
                'text-body-xs px-1.5 py-0.5 rounded-full',
                isActive ? 'bg-accent-muted text-accent-text' : 'bg-surface-secondary text-content-tertiary',
              )}>
                {tab.count}
              </span>
              {isActive && (
                <motion.div
                  layoutId="collection-tab-indicator"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
            </button>
          );
        })}
      </div>

      {!hasContent && (
        <EmptyState
          icon={<LayoutGrid className="w-6 h-6" />}
          title="No items found"
          description="This section has no content yet."
        />
      )}

      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex flex-col gap-6"
      >
        {showScenario && scenarios.length > 0 && (
          <section className="flex flex-col gap-3">
            {activeTab === 'all' && (
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-status-info" />
                <h3 className="text-body-sm font-semibold text-content-primary uppercase tracking-wider">Scenarios</h3>
              </div>
            )}
            <div className="flex flex-col gap-3">
              {scenarios.map((s) => (
                <ScenarioOverviewCard key={s.id} scenario={s} collectionId={collection.id} />
              ))}
            </div>
          </section>
        )}

        {showInterview && interviewItems.length > 0 && (
          <section className="flex flex-col gap-3">
            {activeTab === 'all' && (
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-accent" />
                <h3 className="text-body-sm font-semibold text-content-primary uppercase tracking-wider">Interview Questions</h3>
              </div>
            )}
            <div className="flex flex-col gap-3">
              {interviewItems.map((item) => (
                <PromptItemCard key={item.id} item={item} />
              ))}
            </div>
          </section>
        )}

        {showQuick && quickItems.length > 0 && (
          <section className="flex flex-col gap-3">
            {activeTab === 'all' && (
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-status-success" />
                <h3 className="text-body-sm font-semibold text-content-primary uppercase tracking-wider">Quick Practice</h3>
              </div>
            )}
            <div className="flex flex-col gap-3">
              {quickItems.map((item) => (
                <PromptItemCard key={item.id} item={item} />
              ))}
            </div>
          </section>
        )}
      </motion.div>
    </div>
  );
}
