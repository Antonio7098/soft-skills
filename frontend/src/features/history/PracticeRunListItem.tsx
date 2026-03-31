import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, ChevronDown, ChevronRight, MessageSquare, Play } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { ScoreRing } from '@/design-system/patterns/ScoreRing';
import { useData } from '@/data';
import type { PracticeRunView, PracticeRunItemSummary } from '@/data';

interface PracticeRunListItemProps {
  readonly run: PracticeRunView;
}

export function PracticeRunListItem({ run }: PracticeRunListItemProps) {
  const navigate = useNavigate();
  const data = useData();
  const [expanded, setExpanded] = useState(false);
  const [items, setItems] = useState<PracticeRunItemSummary[]>([]);
  const [itemsLoaded, setItemsLoaded] = useState(false);

  const date = new Date(run.started_at);
  const formatted = date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  const time = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

  useEffect(() => {
    if (expanded && !itemsLoaded && items.length === 0) {
      data.getPracticeRun(run.run_id)
        .then((fullRun) => {
          const assessedItems = (fullRun.items ?? []).filter(item => item.status === 'assessed');
          setItems(assessedItems);
          setItemsLoaded(true);
        })
        .catch(() => setItemsLoaded(true));
    }
  }, [expanded, itemsLoaded, items.length, data, run.run_id]);

  const handleQuestionClick = (item: PracticeRunItemSummary) => {
    const attemptId = item.id;
    if (attemptId) {
      navigate(`/assessment/${attemptId}`);
    }
  };

  return (
    <Card padding="none" className="overflow-hidden">
      <div
        className="flex items-center gap-4 p-4 cursor-pointer hover:bg-surface-secondary/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {run.overall_score !== null && run.overall_score !== undefined ? (
          <ScoreRing score={run.overall_score} size="sm" />
        ) : (
          <div className="w-12 h-12 rounded-full bg-surface-secondary flex items-center justify-center">
            <Play className="w-5 h-5 text-content-tertiary" />
          </div>
        )}

        <div className="flex-1 min-w-0 flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <h4 className="text-body-sm font-medium text-content-primary">
              Practice Session
            </h4>
            {run.overall_score !== null && (
              <Badge variant={run.overall_score >= 4 ? 'success' : run.overall_score >= 3 ? 'accent' : 'warning'} size="sm">
                {run.overall_score}/5
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
            <span>{formatted}</span>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{time}</span>
            </div>
            <span>{run.completed_items}/{run.total_items} completed</span>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          icon={expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
        >
          {run.validated_items} {run.validated_items === 1 ? 'question' : 'questions'}
        </Button>
      </div>

        {expanded && (
        <div className="border-t border-line bg-surface-secondary/30">
          {!itemsLoaded ? (
            <div className="p-4 text-center text-body-xs text-content-tertiary">Loading questions...</div>
          ) : items.length === 0 ? (
            <div className="p-4 text-center text-body-xs text-content-tertiary">No assessed questions yet</div>
          ) : (
            items.map((item, idx) => (
              <div
                key={`${item.id}-${idx}`}
                className="flex items-center gap-3 p-3 px-4 hover:bg-surface-secondary/50 cursor-pointer border-b border-line last:border-b-0"
                onClick={() => handleQuestionClick(item)}
              >
                <MessageSquare className="w-4 h-4 text-content-tertiary shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm text-content-primary truncate">{item.title}</p>
                  <p className="text-body-xs text-content-tertiary truncate">{item.prompt_text}</p>
                </div>
                <Badge variant={item.status === 'assessed' ? 'success' : 'default'} size="sm" className="capitalize">
                  {item.status}
                </Badge>
              </div>
            ))
          )}
        </div>
      )}
    </Card>
  );
}
