import type { DataProvider } from './provider';
import type {
  UserView,
  TaxonomySnapshot,
  CollectionView,
  CollectionListFilters,
  CollectionCreateCommand,
  PromptItemCreateCommand,
  ScenarioCreateCommand,
  RegisterUserCommand,
  UpdateProfileCommand,
  QuickPracticeSessionView,
  StartQuickPracticeSessionCommand,
  SubmitAttemptCommand,
  AttemptView,
  CompetencyProgressView,
  AttemptHistoryItem,
} from './types';
import {
  SEED_SKILLS,
  SEED_COMPETENCIES,
  SEED_RUBRICS,
  SEED_COLLECTIONS,
  SEED_CURRENT_USER,
  SEED_ATTEMPT_HISTORY,
  SEED_COMPETENCY_PROGRESS,
} from './mock-data';

// ---------------------------------------------------------------------------
// MockDataProvider — all data comes from in-memory seed arrays.
// Simulates async API latency for realistic UX.
// ---------------------------------------------------------------------------

let _collections = [...SEED_COLLECTIONS];
let _user = { ...SEED_CURRENT_USER };
let _attempts = [...SEED_ATTEMPT_HISTORY];

function delay(ms = 300): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10);
}

export const mockDataProvider: DataProvider = {
  // --- Auth / Identity -----------------------------------------------------

  async register(cmd: RegisterUserCommand): Promise<UserView> {
    await delay();
    const user: UserView = {
      id: uid(),
      email: cmd.email,
      display_name: cmd.display_name,
      role: cmd.role ?? 'standard_user',
      auth_provider: 'local',
      created_at: new Date().toISOString(),
      profile: {
        target_role: cmd.target_role ?? null,
        goals: cmd.goals ?? [],
        practice_preferences: cmd.practice_preferences ?? {},
      },
    };
    _user = user;
    return user;
  },

  async getMe(): Promise<UserView> {
    await delay(150);
    return _user;
  },

  async updateProfile(cmd: UpdateProfileCommand): Promise<UserView> {
    await delay();
    _user = {
      ..._user,
      profile: {
        target_role: cmd.target_role !== undefined ? cmd.target_role : _user.profile.target_role,
        goals: cmd.goals !== undefined ? cmd.goals ?? [] : _user.profile.goals,
        practice_preferences: cmd.practice_preferences !== undefined
          ? cmd.practice_preferences ?? {}
          : _user.profile.practice_preferences,
      },
    };
    return _user;
  },

  // --- Taxonomy ------------------------------------------------------------

  async getTaxonomy(): Promise<TaxonomySnapshot> {
    await delay(150);
    return {
      skills: SEED_SKILLS,
      competencies: SEED_COMPETENCIES,
      rubrics: SEED_RUBRICS,
    };
  },

  // --- Catalog -------------------------------------------------------------

  async listCollections(filters?: CollectionListFilters): Promise<CollectionView[]> {
    await delay();
    let result = _collections;
    if (filters?.difficulty) {
      result = result.filter((c) => c.difficulty === filters.difficulty);
    }
    if (filters?.skill_slug) {
      result = result.filter((c) => c.target_skill_slugs.includes(filters.skill_slug!));
    }
    if (filters?.competency_slug) {
      result = result.filter((c) => c.target_competency_slugs.includes(filters.competency_slug!));
    }
    if (!filters?.include_private) {
      result = result.filter((c) => c.lifecycle_state === 'published_public');
    }
    return result;
  },

  async getCollection(id: string): Promise<CollectionView> {
    await delay(200);
    const col = _collections.find((c) => c.id === id);
    if (!col) throw new Error(`Collection ${id} not found`);
    return col;
  },

  async createCollection(cmd: CollectionCreateCommand): Promise<CollectionView> {
    await delay();
    const col: CollectionView = {
      id: `col-${uid()}`,
      author_user_id: _user.id,
      title: cmd.title,
      summary: cmd.summary,
      target_audience: cmd.target_audience,
      difficulty: cmd.difficulty,
      lifecycle_state: 'draft',
      verification_state: 'unverified',
      content_format_mix: cmd.content_format_mix ?? [],
      target_skill_slugs: cmd.target_skill_slugs,
      target_competency_slugs: cmd.target_competency_slugs,
      rubric_ids: cmd.rubric_ids,
      prompt_items: [],
      scenarios: [],
    };
    _collections = [..._collections, col];
    return col;
  },

  async addPromptItem(collectionId: string, cmd: PromptItemCreateCommand): Promise<CollectionView> {
    await delay();
    const colIdx = _collections.findIndex((c) => c.id === collectionId);
    if (colIdx === -1) throw new Error(`Collection ${collectionId} not found`);

    const newItem = {
      id: `pi-${uid()}`,
      prompt_type: cmd.prompt_type,
      title: cmd.title,
      prompt_text: cmd.prompt_text,
      difficulty: cmd.difficulty,
      lifecycle_state: 'draft' as const,
      target_skill_slugs: cmd.target_skill_slugs,
      rubric_id: cmd.rubric_id,
    };

    const updated = {
      ..._collections[colIdx]!,
      prompt_items: [..._collections[colIdx]!.prompt_items, newItem],
    };
    _collections = _collections.map((c, i) => (i === colIdx ? updated : c));
    return updated;
  },

  async addScenario(collectionId: string, cmd: ScenarioCreateCommand): Promise<CollectionView> {
    await delay();
    const colIdx = _collections.findIndex((c) => c.id === collectionId);
    if (colIdx === -1) throw new Error(`Collection ${collectionId} not found`);

    const newScenario = {
      id: `sc-${uid()}`,
      title: cmd.title,
      business_context: cmd.business_context,
      learner_objective: cmd.learner_objective,
      constraints: cmd.constraints ?? [],
      stakeholder_tensions: cmd.stakeholder_tensions ?? [],
      lifecycle_state: 'draft' as const,
      target_skill_slugs: cmd.target_skill_slugs,
      rubric_id: cmd.rubric_id,
      mock_company: cmd.mock_company
        ? { id: `mc-${uid()}`, ...cmd.mock_company }
        : null,
      mock_people: (cmd.mock_people ?? []).map((p) => ({
        id: `mp-${uid()}`,
        name: p.name,
        role: p.role,
        goals: p.goals ?? [],
        communication_style: p.communication_style,
        relationship_to_scenario: p.relationship_to_scenario,
      })),
    };

    const updated = {
      ..._collections[colIdx]!,
      scenarios: [..._collections[colIdx]!.scenarios, newScenario],
    };
    _collections = _collections.map((c, i) => (i === colIdx ? updated : c));
    return updated;
  },

  // --- Practice ------------------------------------------------------------

  async startQuickPracticeSession(cmd: StartQuickPracticeSessionCommand): Promise<QuickPracticeSessionView> {
    await delay(200);
    const item = _collections
      .flatMap((c) => c.prompt_items)
      .find((p) => p.id === cmd.prompt_item_id);

    if (!item) throw new Error(`Prompt item ${cmd.prompt_item_id} not found`);

    const sessionId = `sess-${uid()}`;
    const attemptId = `att-${uid()}`;

    return {
      session_id: sessionId,
      attempt_id: attemptId,
      workflow_id: `wf-${uid()}`,
      status: 'active',
      prompt: {
        content_item_id: item.id,
        prompt_type: item.prompt_type,
        title: item.title,
        prompt_text: item.prompt_text,
        difficulty: item.difficulty,
        delivery_version: 'quick-practice.delivery.v1',
        target_skill_slugs: item.target_skill_slugs,
        rubric_id: item.rubric_id,
        rubric_version: 'v1',
      },
      started_at: new Date().toISOString(),
      trace_id: `trace-${uid()}`,
    };
  },

  async submitAttempt(attemptId: string, cmd: SubmitAttemptCommand): Promise<AttemptView> {
    await delay(1500); // simulate LLM scoring latency

    // find a random prompt to build assessment against
    const promptItem = _collections.flatMap((c) => c.prompt_items)[0]!;
    const score = Math.floor(Math.random() * 3) + 3; // 3-5

    const prompt = {
      content_item_id: promptItem.id,
      prompt_type: promptItem.prompt_type,
      title: promptItem.title,
      prompt_text: promptItem.prompt_text,
      difficulty: promptItem.difficulty,
      delivery_version: 'quick-practice.delivery.v1',
      target_skill_slugs: promptItem.target_skill_slugs,
      rubric_id: promptItem.rubric_id,
      rubric_version: 'v1',
    };

    const skill_scores = promptItem.target_skill_slugs.map((slug) => ({
      skill_slug: slug,
      score: Math.max(1, Math.min(5, score + (Math.random() > 0.5 ? 0 : -1))),
      rationale: `Demonstrated ${score >= 3 ? 'solid' : 'developing'} ${slug.replace(/-/g, ' ')}.`,
    }));

    const evidence = promptItem.target_skill_slugs.slice(0, 2).map((slug) => ({
      skill_slug: slug,
      quote: cmd.response_text.slice(0, 80),
      explanation: `This excerpt demonstrates ${slug.replace(/-/g, ' ')} through the learner's approach.`,
    }));

    const attempt: AttemptView = {
      id: attemptId,
      session_id: `sess-${uid()}`,
      workflow_id: `wf-${uid()}`,
      status: 'assessed',
      response_mode: 'text',
      response_text: cmd.response_text,
      last_error_code: null,
      submitted_at: new Date().toISOString(),
      assessed_at: new Date().toISOString(),
      prompt,
      assessment: {
        assessment_id: `assess-${uid()}`,
        attempt_id: attemptId,
        session_id: `sess-${uid()}`,
        validation_status: 'validated',
        prompt_version: 'assessment.quick-practice.v1',
        rubric_id: promptItem.rubric_id,
        rubric_version: 'v1',
        schema_version: 'quick-practice-assessment-output.v1',
        config_version: 'quick-practice-marking-config.v1',
        provider: 'mock',
        model_slug: 'mock-v1',
        overall_score: score,
        skill_scores,
        evidence,
        rationale: score >= 4
          ? 'The response effectively addresses the prompt with clear reasoning and structure.'
          : 'The response partially addresses the prompt with a reasonable approach that could be more detailed.',
        strengths: score >= 3 ? ['Clear communication', 'Relevant context'] : ['Attempted to address the prompt'],
        weaknesses: score < 4 ? ['Add more specific examples', 'Strengthen the conclusion'] : ['Minor refinements possible'],
        next_actions: ['Practice under time pressure', 'Review the relevant framework'],
        trace_id: `trace-${uid()}`,
        pipeline_run_id: `run-${uid()}`,
        rejection_code: null,
        created_at: new Date().toISOString(),
      },
    };

    _attempts = [
      {
        id: attemptId,
        session_id: attempt.session_id,
        title: prompt.title,
        practice_type: 'quick_practice',
        score,
        skill_slugs: prompt.target_skill_slugs,
        created_at: attempt.assessed_at!,
        status: 'assessed',
      },
      ..._attempts,
    ];

    return attempt;
  },

  async getAttempt(attemptId: string): Promise<AttemptView> {
    await delay(200);
    const historyItem = _attempts.find((a) => a.id === attemptId);
    if (!historyItem) throw new Error(`Attempt ${attemptId} not found`);

    const promptItem = _collections.flatMap((c) => c.prompt_items).find(
      (p) => p.title === historyItem.title,
    ) ?? _collections.flatMap((c) => c.prompt_items)[0]!;

    return {
      id: historyItem.id,
      session_id: historyItem.session_id,
      workflow_id: `wf-${historyItem.id}`,
      status: historyItem.status,
      response_mode: 'text',
      response_text: 'This is a saved response for review.',
      last_error_code: null,
      submitted_at: historyItem.created_at,
      assessed_at: historyItem.created_at,
      prompt: {
        content_item_id: promptItem.id,
        prompt_type: promptItem.prompt_type,
        title: promptItem.title,
        prompt_text: promptItem.prompt_text,
        difficulty: promptItem.difficulty,
        delivery_version: 'quick-practice.delivery.v1',
        target_skill_slugs: promptItem.target_skill_slugs,
        rubric_id: promptItem.rubric_id,
        rubric_version: 'v1',
      },
      assessment: {
        assessment_id: `assess-${historyItem.id}`,
        attempt_id: historyItem.id,
        session_id: historyItem.session_id,
        validation_status: 'validated',
        prompt_version: 'assessment.quick-practice.v1',
        rubric_id: promptItem.rubric_id,
        rubric_version: 'v1',
        schema_version: 'quick-practice-assessment-output.v1',
        config_version: 'quick-practice-marking-config.v1',
        provider: 'mock',
        model_slug: 'mock-v1',
        overall_score: historyItem.score,
        skill_scores: historyItem.skill_slugs.map((slug) => ({
          skill_slug: slug,
          score: historyItem.score,
          rationale: `Consistent ${slug.replace(/-/g, ' ')} performance.`,
        })),
        evidence: historyItem.skill_slugs.slice(0, 2).map((slug) => ({
          skill_slug: slug,
          quote: 'Relevant excerpt from the stored response.',
          explanation: `Demonstrates ${slug.replace(/-/g, ' ')}.`,
        })),
        rationale: `Score of ${historyItem.score}/5 based on rubric criteria.`,
        strengths: ['Structured approach', 'Clear reasoning'],
        weaknesses: historyItem.score < 4 ? ['Could be more specific'] : [],
        next_actions: ['Continue practicing similar prompts'],
        trace_id: `trace-${historyItem.id}`,
        pipeline_run_id: `run-${historyItem.id}`,
        rejection_code: null,
        created_at: historyItem.created_at,
      },
    };
  },

  // --- Progress ------------------------------------------------------------

  async getCompetencyProgress(_userId: string): Promise<CompetencyProgressView[]> {
    await delay(200);
    return SEED_COMPETENCY_PROGRESS;
  },

  async getAttemptHistory(_userId: string): Promise<AttemptHistoryItem[]> {
    await delay(150);
    return _attempts;
  },
};
