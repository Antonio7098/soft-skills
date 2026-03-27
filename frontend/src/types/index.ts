import type { ReactNode } from 'react';

export interface PracticeMode {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly icon: ReactNode;
  readonly duration: string;
  readonly difficulty: string;
  readonly color: string;
  readonly features: readonly string[];
}

export interface RecentSession {
  readonly id: number;
  readonly type: string;
  readonly title: string;
  readonly date: string;
  readonly score: number;
  readonly duration: string;
  readonly skills: readonly string[];
  readonly status: string;
}

export interface RecommendedPractice {
  readonly id: number;
  readonly title: string;
  readonly description: string;
  readonly type: string;
  readonly duration: string;
  readonly difficulty: string;
  readonly reason: string;
  readonly skills: readonly string[];
}

export interface SkillFocus {
  readonly skill: string;
  readonly level: number;
  readonly focus: 'High' | 'Medium' | 'Low';
  readonly trend: 'up' | 'down' | 'stable';
}

export interface RecentActivity {
  readonly title: string;
  readonly score: number;
  readonly date: string;
  readonly type: string;
}

export interface Collection {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly author: string;
  readonly authorAvatar: string | null;
  readonly items: number;
  readonly duration: string;
  readonly difficulty: string;
  readonly rating: number;
  readonly reviews: number;
  readonly tags: readonly string[];
  readonly verified: boolean;
  readonly featured: boolean;
}

export interface CompetencyProgress {
  readonly name: string;
  readonly level: string;
  readonly label: string;
  readonly skills: readonly SkillBar[];
}

export interface SkillBar {
  readonly name: string;
  readonly value: number;
}

export interface NavRoute {
  readonly path: string;
  readonly label: string;
  readonly icon: React.ComponentType<{ className?: string }>;
}
