import type { RubricCriterionView, RubricType } from './types';

export function getRubricType(rubricId: string): RubricType {
  if (rubricId.startsWith('quick_practice_text')) return 'quick_practice';
  if (rubricId.startsWith('interview_text')) return 'interview';
  if (rubricId.startsWith('scenario_text')) return 'scenario';
  return 'quick_practice';
}

export function isBinaryRubric(rubricId: string, rubricCriteria: RubricCriterionView[]): boolean {
  const criteria = rubricCriteria.filter((c) => c.rubric_id === rubricId);
  if (criteria.length === 0) return false;
  const levels = Object.keys(criteria[0]!.levels);
  return levels.length === 2 && levels.includes('level_1') && levels.includes('level_2');
}

export function getRubricCriteriaForSkill(
  rubricId: string,
  skillSlug: string,
  rubricCriteria: RubricCriterionView[],
): RubricCriterionView | undefined {
  return rubricCriteria.find((c) => c.rubric_id === rubricId && c.skill_slug === skillSlug);
}

export function getLevelDescription(
  rubricId: string,
  skillSlug: string,
  score: number,
  rubricCriteria: RubricCriterionView[],
): string {
  const criterion = getRubricCriteriaForSkill(rubricId, skillSlug, rubricCriteria);
  if (!criterion) return `Score ${score}`;
  const levelKey = `level_${score}`;
  return criterion.levels[levelKey]?.description ?? `Score ${score}`;
}

export function getRubricMaxScore(rubricId: string, rubricCriteria: RubricCriterionView[]): number {
  const criteria = rubricCriteria.filter((c) => c.rubric_id === rubricId);
  if (criteria.length === 0) return 5;
  const levels = Object.keys(criteria[0]!.levels);
  return levels.length;
}

export function formatScore(rubricId: string, score: number, _rubricCriteria?: RubricCriterionView[]): string {
  const rubricType = getRubricType(rubricId);
  if (rubricType === 'quick_practice') {
    return score >= 2 ? 'Pass' : 'Fail';
  }
  return `${score}/5`;
}

export function getScoreLabel(rubricId: string, score: number): string {
  const rubricType = getRubricType(rubricId);
  if (rubricType === 'quick_practice') {
    return score >= 2 ? 'Pass' : 'Fail';
  }
  if (score >= 5) return 'Excellent';
  if (score >= 4) return 'Strong';
  if (score >= 3) return 'Adequate';
  if (score >= 2) return 'Developing';
  return 'Needs Work';
}
