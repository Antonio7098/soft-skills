import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, ChevronDown, ChevronRight, MessageSquare } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { ScoreRing } from '@/design-system/patterns/ScoreRing';
import { getScoreVariant } from '@/lib/variant-helpers';
import type { AttemptHistoryItem, AttemptQuestionSummary } from '@/data';

interface AttemptListItemProps {
  readonly attempt: AttemptHistoryItem;
}

export function AttemptListItem({ attempt }: AttemptListItemProps) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const hasQuestions = attempt.questions && attempt.questions.length > 0;
  const date = new Date(attempt.created_at);
  const formatted = date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  const time = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

  const handleQuestionClick = (question: AttemptQuestionSummary) => {
    navigate(`/assessment/${attempt.id}?questionIndex=${question.question_index}`);
  };

  return (
    <Card padding="none" className="overflow-hidden">
      <div 
        className="flex items-center gap-4 p-4 cursor-pointer hover:bg-surface-secondary/50 transition-colors"
        onClick={() => navigate(`/assessment/${attempt.id}`)}
      >
        <ScoreRing score={attempt.score} size="sm" />

        <div className="flex-1 min-w-0 flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <h4 className="text-body-sm font-medium text-content-primary truncate">{attempt.title}</h4>
            <Badge variant={getScoreVariant(attempt.score)} size="sm">
              {attempt.score}/5
            </Badge>
          </div>
          <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
            <span>{formatted}</span>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{time}</span>
            </div>
            <Badge variant="default" size="sm" className="capitalize">
              {attempt.practice_type.replace(/_/g, ' ')}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-1">
            {attempt.skill_slugs.slice(0, 4).map((slug) => (
              <Badge key={slug} variant="default" size="sm">
                {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </Badge>
            ))}
          </div>
        </div>

        {hasQuestions && (
          <Button 
            variant="ghost" 
            size="sm"
            icon={expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
          >
            {attempt.questions!.length} {attempt.questions!.length === 1 ? 'question' : 'questions'}
          </Button>
        )}

        <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); navigate(`/assessment/${attempt.id}`); }}>
          Review
        </Button>
      </div>

      {expanded && hasQuestions && (
        <div className="border-t border-line bg-surface-secondary/30">
          {attempt.questions!.map((question, idx) => (
            <div
              key={question.question_index}
              className="flex items-center gap-3 p-3 px-4 hover:bg-surface-secondary/50 cursor-pointer border-b border-line last:border-b-0"
              onClick={() => handleQuestionClick(question)}
            >
              <MessageSquare className="w-4 h-4 text-content-tertiary shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-body-sm text-content-primary truncate">{question.question_text}</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {question.skill_slugs.slice(0, 2).map((slug) => (
                    <Badge key={slug} variant="default" size="sm">
                      {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    </Badge>
                  ))}
                </div>
              </div>
              {question.score !== null && (
                <Badge variant={getScoreVariant(question.score)} size="sm">
                  {question.score}/5
                </Badge>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
