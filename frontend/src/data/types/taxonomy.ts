export interface SkillView {
  readonly slug: string;
  readonly name: string;
  readonly description: string;
}

export interface CompetencyView {
  readonly slug: string;
  readonly name: string;
  readonly description: string;
  readonly skill_slugs: string[];
  readonly skills: SkillView[];
}

export interface RubricView {
  readonly rubric_id: string;
  readonly family: string;
  readonly version: string;
  readonly content_type: string;
  readonly schema_version: string;
  readonly name: string;
}

export interface RubricLevel {
  readonly description: string;
  readonly examples: string[];
}

export interface RubricCriterionView {
  readonly id: string;
  readonly rubric_id: string;
  readonly rubric_version: string;
  readonly criterion_ref: string;
  readonly skill_slug: string;
  readonly title: string;
  readonly description: string;
  readonly weight: number;
  readonly required: boolean;
  readonly position: number;
  readonly levels: Record<string, RubricLevel>;
}

export interface OrgSkillView {
  readonly slug: string;
  readonly name: string;
  readonly description: string;
  readonly organisation_id: string;
  readonly skill_slug?: string;
}

export interface OrgCompetencyView {
  readonly slug: string;
  readonly name: string;
  readonly description: string;
  readonly skill_slugs: string[];
  readonly organisation_id: string;
}

export interface OrgRubricView {
  readonly rubric_id: string;
  readonly family: string;
  readonly version: string;
  readonly content_type: string;
  readonly schema_version: string;
  readonly name: string;
  readonly criteria: string[];
  readonly organisation_id: string;
}

export interface TaxonomySnapshot {
  readonly skills: SkillView[];
  readonly competencies: CompetencyView[];
  readonly rubrics: RubricView[];
  readonly rubric_criteria: RubricCriterionView[];
}
