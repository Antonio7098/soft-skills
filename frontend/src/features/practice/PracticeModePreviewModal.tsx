import { Modal, ModalFooter, ModalSection } from '@/design-system/primitives/Modal';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { Brain, Target, Briefcase, Mic, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/cn';
import { getDifficultyVariant } from '@/lib/variant-helpers';

interface PracticeModePreviewModalProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly modeId: string;
  readonly modeTitle: string;
  readonly modeColor: string;
  readonly onStartPractice: () => void;
}

interface SampleQuestion {
  readonly question: string;
  readonly skills: string[];
  readonly difficulty: string;
}

const SAMPLE_QUESTIONS: Record<string, SampleQuestion[]> = {
  interview: [
    {
      question: 'Tell me about a time you had to manage a difficult stakeholder. How did you approach the situation?',
      skills: ['Stakeholder Management', 'Communication', 'Empathy'],
      difficulty: 'Intermediate',
    },
    {
      question: 'Describe a situation where you had to make a decision with incomplete information. What was your process?',
      skills: ['Decision Making', 'Managing Ambiguity', 'Problem Solving'],
      difficulty: 'Advanced',
    },
    {
      question: 'Give me an example of how you handled a conflict within your team. What was the outcome?',
      skills: ['Conflict Resolution', 'Teamwork', 'Communication'],
      difficulty: 'Intermediate',
    },
    {
      question: 'Tell me about a time you had to adapt your communication style for different audiences.',
      skills: ['Communication', 'Adaptability', 'Executive Presence'],
      difficulty: 'Intermediate',
    },
  ],
  scenario: [
    {
      question: 'Your project sponsor is unhappy with the latest sprint demo. The reporting module has significant gaps, and the deadline cannot be moved. How do you handle this conversation?',
      skills: ['Stakeholder Management', 'Expectation Setting', 'Negotiation'],
      difficulty: 'Advanced',
    },
    {
      question: 'You discover a critical compliance issue two weeks before a product launch. The engineering team wants to ship, but legal has outstanding concerns. What steps do you take?',
      skills: ['Risk Management', 'Communication', 'Decision Making'],
      difficulty: 'Advanced',
    },
    {
      question: 'Two senior stakeholders have conflicting priorities for your team. Both claim their work is urgent. How do you navigate this?',
      skills: ['Prioritization', 'Stakeholder Management', 'Conflict Resolution'],
      difficulty: 'Advanced',
    },
  ],
  quick: [
    {
      question: 'Your project is 2 weeks behind schedule due to a dependency on another team. Write a concise executive summary for the stakeholder meeting in 10 minutes.',
      skills: ['Executive Summary', 'Concise Communication', 'Structured Communication'],
      difficulty: 'Intermediate',
    },
    {
      question: 'A senior stakeholder asks you to add three new features two days before release. Your team is at capacity. Draft your response.',
      skills: ['Expectation Setting', 'Negotiation', 'Conflict Handling'],
      difficulty: 'Advanced',
    },
    {
      question: 'During standup, a junior developer mentions being stuck for 3 days without asking for help. Respond as their lead.',
      skills: ['Active Listening', 'Empathy', 'Structured Communication'],
      difficulty: 'Beginner',
    },
    {
      question: 'You have three urgent tasks: a production bug, a client demo tomorrow, and an immovable compliance deadline. You can only do one. Explain your decision.',
      skills: ['Prioritization', 'Decision Justification', 'Concise Communication'],
      difficulty: 'Advanced',
    },
  ],
  speech: [
    {
      question: 'Deliver a 2-minute update to the executive team about a project that is over budget but on track for key deliverables.',
      skills: ['Executive Presence', 'Clarity', 'Structured Communication'],
      difficulty: 'Intermediate',
    },
    {
      question: 'Present a complex technical concept to a non-technical audience in under 3 minutes. Focus on clarity and impact.',
      skills: ['Communication', 'Clarity', 'Audience Adaptation'],
      difficulty: 'Intermediate',
    },
    {
      question: 'Give a 90-second pitch for why your team should adopt a new process. Address potential objections proactively.',
      skills: ['Persuasion', 'Concise Communication', 'Executive Presence'],
      difficulty: 'Advanced',
    },
  ],
};

const MODE_ICONS: Record<string, React.ReactNode> = {
  interview: <Briefcase className="w-5 h-5" />,
  scenario: <Target className="w-5 h-5" />,
  quick: <Brain className="w-5 h-5" />,
  speech: <Mic className="w-5 h-5" />,
};

export function PracticeModePreviewModal({
  isOpen,
  onClose,
  modeId,
  modeTitle,
  modeColor,
  onStartPractice,
}: PracticeModePreviewModalProps) {
  const questions = SAMPLE_QUESTIONS[modeId] ?? [];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={modeTitle}
      description="Here are some example questions you might encounter. Ready to practice?"
      size="lg"
    >
      <ModalSection>
        <div className="flex flex-col gap-3">
          {questions.map((q, index) => (
            <Card key={index} variant="outlined" padding="md" className="flex flex-col gap-3">
              <div className="flex items-start gap-3">
                <div className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
                  `bg-${modeColor}/10 text-${modeColor}`,
                )}>
                  {MODE_ICONS[modeId]}
                </div>
                <div className="flex-1">
                  <p className="text-body-md text-content-primary">{q.question}</p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 pl-11">
                <Badge variant={getDifficultyVariant(q.difficulty)} size="sm">
                  {q.difficulty}
                </Badge>
                {q.skills.map((skill) => (
                  <Badge key={skill} variant="default" size="sm">
                    {skill}
                  </Badge>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </ModalSection>

      <ModalFooter>
        <Button variant="ghost" onClick={onClose}>
          Close
        </Button>
        <Button
          variant="primary"
          icon={<ArrowRight className="w-4 h-4" />}
          onClick={onStartPractice}
        >
          Start Practice
        </Button>
      </ModalFooter>
    </Modal>
  );
}
