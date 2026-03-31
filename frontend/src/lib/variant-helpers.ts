import type { BadgeVariant } from '@/design-system/primitives/Badge';

type Difficulty = 'Beginner' | 'Intermediate' | 'Advanced';
type SessionType = 'Interview' | 'Scenario' | 'Quick Practice' | 'Speech Exercise';
type FocusLevel = 'High' | 'Medium' | 'Low';

const difficultyToVariant: Record<Difficulty, BadgeVariant> = {
  Beginner: 'success',
  Intermediate: 'warning',
  Advanced: 'error',
};

const sessionTypeToVariant: Record<SessionType, BadgeVariant> = {
  Interview: 'accent',
  Scenario: 'info',
  'Quick Practice': 'success',
  'Speech Exercise': 'warning',
};

const focusToVariant: Record<FocusLevel, BadgeVariant> = {
  High: 'error',
  Medium: 'warning',
  Low: 'success',
};

export function getDifficultyVariant(difficulty: string): BadgeVariant {
  return difficultyToVariant[difficulty as Difficulty] ?? 'default';
}

export function getSessionTypeVariant(type: string): BadgeVariant {
  return sessionTypeToVariant[type as SessionType] ?? 'default';
}

export function getFocusVariant(focus: string): BadgeVariant {
  return focusToVariant[focus as FocusLevel] ?? 'default';
}

type DomainDifficulty = 'introductory' | 'intermediate' | 'advanced';

const domainDifficultyToVariant: Record<DomainDifficulty, BadgeVariant> = {
  introductory: 'success',
  intermediate: 'warning',
  advanced: 'error',
};

export function getDomainDifficultyVariant(difficulty: string): BadgeVariant {
  return domainDifficultyToVariant[difficulty as DomainDifficulty] ?? 'default';
}

export function getScoreVariant(score: number): BadgeVariant {
  if (score >= 4) return 'success';
  if (score >= 3) return 'warning';
  return 'error';
}
