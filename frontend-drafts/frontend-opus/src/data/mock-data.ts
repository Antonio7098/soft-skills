import type {
  UserView,
  CollectionView,
  CompetencyProgressView,
  AttemptHistoryItem,
  SkillView,
  CompetencyView,
  RubricView,
  MockCompanyView,
  MockPersonView,
  PromptItemView,
  ScenarioView,
} from './types';

// ---------------------------------------------------------------------------
// Seed data drawn from backend application/taxonomy.py and MVP spec
// ---------------------------------------------------------------------------

export const SEED_SKILLS: SkillView[] = [
  { slug: 'active-listening', name: 'Active Listening', description: 'Demonstrating genuine attention and understanding in conversations.' },
  { slug: 'structured-communication', name: 'Structured Communication', description: 'Organizing thoughts logically and presenting them clearly.' },
  { slug: 'concise-explanation', name: 'Concise Explanation', description: 'Conveying complex ideas in a clear, brief manner.' },
  { slug: 'empathy', name: 'Empathy', description: 'Recognizing and responding to the emotions and perspectives of others.' },
  { slug: 'expectation-setting', name: 'Expectation Setting', description: 'Defining clear, realistic expectations with stakeholders.' },
  { slug: 'prioritization-under-pressure', name: 'Prioritization Under Pressure', description: 'Making sound prioritization decisions when time or resources are constrained.' },
  { slug: 'conflict-handling', name: 'Conflict Handling', description: 'Navigating and resolving disagreements constructively.' },
  { slug: 'negotiation', name: 'Negotiation', description: 'Reaching mutually beneficial outcomes through discussion and compromise.' },
  { slug: 'executive-summary', name: 'Executive Summary', description: 'Distilling key information for senior audiences.' },
  { slug: 'decision-justification', name: 'Decision Justification', description: 'Articulating the reasoning behind decisions clearly.' },
];

export const SEED_COMPETENCIES: CompetencyView[] = [
  { slug: 'stakeholder-management', name: 'Stakeholder Management', description: 'Managing relationships with stakeholders effectively.', skill_slugs: ['active-listening', 'empathy', 'expectation-setting', 'negotiation'] },
  { slug: 'communication', name: 'Communication', description: 'Conveying information clearly and effectively.', skill_slugs: ['structured-communication', 'concise-explanation', 'executive-summary'] },
  { slug: 'teamwork', name: 'Teamwork', description: 'Collaborating effectively with others.', skill_slugs: ['active-listening', 'empathy', 'conflict-handling'] },
  { slug: 'prioritization', name: 'Prioritization', description: 'Identifying and focusing on the most important work.', skill_slugs: ['prioritization-under-pressure', 'decision-justification', 'executive-summary'] },
  { slug: 'professionalism', name: 'Professionalism', description: 'Conducting oneself with competence and integrity.', skill_slugs: ['expectation-setting', 'concise-explanation', 'conflict-handling'] },
  { slug: 'problem-solving', name: 'Problem Solving', description: 'Analyzing issues and developing effective solutions.', skill_slugs: ['structured-communication', 'decision-justification', 'executive-summary'] },
  { slug: 'adaptability', name: 'Adaptability', description: 'Adjusting approach based on changing circumstances.', skill_slugs: ['active-listening', 'prioritization-under-pressure', 'decision-justification'] },
  { slug: 'managing-ambiguity', name: 'Managing Ambiguity', description: 'Making progress when information is incomplete.', skill_slugs: ['expectation-setting', 'prioritization-under-pressure', 'negotiation'] },
];

export const SEED_RUBRICS: RubricView[] = [
  { rubric_id: 'quick_practice_text', family: 'quick_practice_text', version: 'v1', content_type: 'quick_practice_prompt', schema_version: 'quick-practice-assessment-output.v1', name: 'Quick Practice (Text)' },
  { rubric_id: 'scenario_text', family: 'scenario_text', version: 'v1', content_type: 'scenario_step', schema_version: 'scenario-assessment-output.v1', name: 'Scenario (Text)' },
  { rubric_id: 'interview_text', family: 'interview_text', version: 'v1', content_type: 'interview_prompt', schema_version: 'interview-assessment-output.v1', name: 'Interview (Text)' },
];

// --- Mock companies & people -----------------------------------------------

const MOCK_COMPANY_NEXATECH: MockCompanyView = {
  id: 'mc-001',
  name: 'NexaTech Solutions',
  industry: 'Enterprise Software',
  operating_context: 'A mid-size SaaS company undergoing digital transformation, serving enterprise clients in financial services.',
};

const MOCK_COMPANY_GREENFIELD: MockCompanyView = {
  id: 'mc-002',
  name: 'Greenfield Health',
  industry: 'Healthcare Technology',
  operating_context: 'A healthcare startup building AI-powered diagnostic tools for regional hospitals.',
};

const MOCK_PERSON_SARAH: MockPersonView = {
  id: 'mp-001',
  name: 'Sarah Mitchell',
  role: 'VP of Engineering',
  goals: ['Reduce technical debt', 'Ship the platform migration on time'],
  communication_style: 'Direct and data-driven; prefers structured updates.',
  relationship_to_scenario: 'Your direct manager who sets your quarterly priorities.',
};

const MOCK_PERSON_JAMES: MockPersonView = {
  id: 'mp-002',
  name: 'James Okafor',
  role: 'Client Director',
  goals: ['Maintain client satisfaction', 'Expand the account'],
  communication_style: 'Diplomatic and relationship-focused.',
  relationship_to_scenario: 'The client stakeholder who is unhappy with recent delivery delays.',
};

const MOCK_PERSON_PRIYA: MockPersonView = {
  id: 'mp-003',
  name: 'Dr. Priya Sharma',
  role: 'Chief Medical Officer',
  goals: ['Improve diagnostic accuracy', 'Ensure regulatory compliance'],
  communication_style: 'Evidence-based and cautious; asks detailed questions.',
  relationship_to_scenario: 'The clinical advisor whose approval is required for launch.',
};

// --- Prompt items -----------------------------------------------------------

const PROMPT_ITEMS: PromptItemView[] = [
  {
    id: 'pi-001',
    prompt_type: 'quick_practice_prompt',
    title: 'Executive Summary: Project Status',
    prompt_text: 'Your project is 2 weeks behind schedule due to a key dependency on another team. The stakeholder meeting is in 10 minutes. Write a concise executive summary explaining the situation, impact, and your proposed mitigation plan.',
    difficulty: 'intermediate',
    lifecycle_state: 'published_public',
    target_skill_slugs: ['executive-summary', 'concise-explanation', 'structured-communication'],
    rubric_id: 'quick_practice_text',
  },
  {
    id: 'pi-002',
    prompt_type: 'quick_practice_prompt',
    title: 'Saying No to Scope Creep',
    prompt_text: 'A senior stakeholder has asked you to add three new features to the current sprint, two days before the release deadline. The team is already at capacity. Write your response explaining why this is not feasible and propose an alternative.',
    difficulty: 'advanced',
    lifecycle_state: 'published_public',
    target_skill_slugs: ['expectation-setting', 'negotiation', 'conflict-handling'],
    rubric_id: 'quick_practice_text',
  },
  {
    id: 'pi-003',
    prompt_type: 'quick_practice_prompt',
    title: 'Active Listening: Team Standup',
    prompt_text: 'During a standup, a junior developer mentions they have been stuck on the same task for 3 days but did not ask for help. As their lead, write a response that demonstrates active listening and helps them move forward without making them feel inadequate.',
    difficulty: 'introductory',
    lifecycle_state: 'published_public',
    target_skill_slugs: ['active-listening', 'empathy', 'structured-communication'],
    rubric_id: 'quick_practice_text',
  },
  {
    id: 'pi-004',
    prompt_type: 'quick_practice_prompt',
    title: 'Prioritization Under Pressure',
    prompt_text: 'You have three urgent tasks: a production bug affecting 10% of users, a demo for a potential enterprise client tomorrow, and a compliance deadline that cannot be moved. You can only do one today. Explain your prioritization decision.',
    difficulty: 'advanced',
    lifecycle_state: 'published_public',
    target_skill_slugs: ['prioritization-under-pressure', 'decision-justification', 'concise-explanation'],
    rubric_id: 'quick_practice_text',
  },
  {
    id: 'pi-005',
    prompt_type: 'interview_prompt',
    title: 'Tell me about a time you handled conflict',
    prompt_text: 'Describe a situation where you had a disagreement with a colleague about a technical approach. How did you handle it, and what was the outcome?',
    difficulty: 'intermediate',
    lifecycle_state: 'published_public',
    target_skill_slugs: ['conflict-handling', 'negotiation', 'structured-communication'],
    rubric_id: 'interview_text',
  },
  {
    id: 'pi-006',
    prompt_type: 'interview_prompt',
    title: 'Describe a time you managed competing priorities',
    prompt_text: 'Tell me about a time when you had multiple high-priority tasks with the same deadline. How did you decide what to focus on?',
    difficulty: 'intermediate',
    lifecycle_state: 'published_public',
    target_skill_slugs: ['prioritization-under-pressure', 'decision-justification', 'expectation-setting'],
    rubric_id: 'interview_text',
  },
];

// --- Scenarios --------------------------------------------------------------

const SCENARIOS: ScenarioView[] = [
  {
    id: 'sc-001',
    title: 'The Unhappy Sponsor',
    business_context: 'NexaTech Solutions is midway through a platform migration for a major financial services client. The latest sprint demo revealed significant gaps in the reporting module.',
    learner_objective: 'De-escalate the sponsor\'s frustration, acknowledge the gaps, and present a credible recovery plan.',
    constraints: ['Cannot extend the deadline', 'Cannot add more engineers mid-sprint', 'Client contract has a penalty clause'],
    stakeholder_tensions: ['Sponsor wants immediate fixes', 'Engineering team is already stretched', 'Contractual obligations create pressure'],
    lifecycle_state: 'published_public',
    target_skill_slugs: ['empathy', 'expectation-setting', 'negotiation', 'conflict-handling'],
    rubric_id: 'scenario_text',
    mock_company: MOCK_COMPANY_NEXATECH,
    mock_people: [MOCK_PERSON_JAMES, MOCK_PERSON_SARAH],
  },
  {
    id: 'sc-002',
    title: 'AI Model Compliance Review',
    business_context: 'Greenfield Health is preparing to launch an AI-powered diagnostic assistant. The CMO has requested a compliance review before go-live.',
    learner_objective: 'Present the model\'s capabilities and limitations transparently while building confidence in the compliance posture.',
    constraints: ['Regulatory approval pending', 'Must address bias concerns', 'Limited clinical trial data'],
    stakeholder_tensions: ['CMO is risk-averse', 'Engineering wants to ship', 'Legal has outstanding questions'],
    lifecycle_state: 'published_public',
    target_skill_slugs: ['structured-communication', 'concise-explanation', 'expectation-setting', 'empathy'],
    rubric_id: 'scenario_text',
    mock_company: MOCK_COMPANY_GREENFIELD,
    mock_people: [MOCK_PERSON_PRIYA],
  },
];

// --- Collections ------------------------------------------------------------

export const SEED_COLLECTIONS: CollectionView[] = [
  {
    id: 'col-001',
    author_user_id: 'user-001',
    title: 'Consultancy Fundamentals',
    summary: 'Core practice for building foundational consultancy skills across communication, prioritization, and stakeholder management.',
    target_audience: 'Junior consultants and early-career professionals',
    difficulty: 'introductory',
    lifecycle_state: 'published_public',
    verification_state: 'verified',
    content_format_mix: ['quick_practice_prompt', 'interview_prompt'],
    target_skill_slugs: ['structured-communication', 'concise-explanation', 'active-listening', 'expectation-setting'],
    target_competency_slugs: ['communication', 'stakeholder-management'],
    rubric_ids: ['quick_practice_text', 'interview_text'],
    prompt_items: [PROMPT_ITEMS[0]!, PROMPT_ITEMS[2]!, PROMPT_ITEMS[4]!],
    scenarios: [],
  },
  {
    id: 'col-002',
    author_user_id: 'user-001',
    title: 'Stakeholder Navigation',
    summary: 'Master managing complex stakeholder relationships through realistic scenarios and targeted practice.',
    target_audience: 'Consultants and client-facing tech professionals',
    difficulty: 'intermediate',
    lifecycle_state: 'published_public',
    verification_state: 'verified',
    content_format_mix: ['quick_practice_prompt', 'scenario_step', 'interview_prompt'],
    target_skill_slugs: ['empathy', 'negotiation', 'conflict-handling', 'expectation-setting'],
    target_competency_slugs: ['stakeholder-management', 'teamwork'],
    rubric_ids: ['quick_practice_text', 'scenario_text', 'interview_text'],
    prompt_items: [PROMPT_ITEMS[1]!],
    scenarios: [SCENARIOS[0]!],
  },
  {
    id: 'col-003',
    author_user_id: 'user-002',
    title: 'AI Delivery Under Pressure',
    summary: 'High-stakes AI project scenarios with tight deadlines, compliance constraints, and difficult stakeholders.',
    target_audience: 'AI consultants and tech leads',
    difficulty: 'advanced',
    lifecycle_state: 'published_public',
    verification_state: 'verified',
    content_format_mix: ['quick_practice_prompt', 'scenario_step'],
    target_skill_slugs: ['prioritization-under-pressure', 'decision-justification', 'structured-communication', 'concise-explanation'],
    target_competency_slugs: ['prioritization', 'problem-solving', 'adaptability'],
    rubric_ids: ['quick_practice_text', 'scenario_text'],
    prompt_items: [PROMPT_ITEMS[3]!],
    scenarios: [SCENARIOS[1]!],
  },
  {
    id: 'col-004',
    author_user_id: 'user-003',
    title: 'Behavioural Interview Prep',
    summary: 'Practice common behavioural interview questions with structured STAR-method feedback.',
    target_audience: 'Job seekers preparing for tech and consultancy interviews',
    difficulty: 'intermediate',
    lifecycle_state: 'published_public',
    verification_state: 'unverified',
    content_format_mix: ['interview_prompt'],
    target_skill_slugs: ['structured-communication', 'conflict-handling', 'prioritization-under-pressure', 'decision-justification'],
    target_competency_slugs: ['communication', 'problem-solving'],
    rubric_ids: ['interview_text'],
    prompt_items: [PROMPT_ITEMS[4]!, PROMPT_ITEMS[5]!],
    scenarios: [],
  },
  {
    id: 'col-005',
    author_user_id: 'user-001',
    title: 'Executive Communication Mastery',
    summary: 'Practice delivering clear, impactful messages to senior leadership under time pressure.',
    target_audience: 'Senior consultants and managers',
    difficulty: 'advanced',
    lifecycle_state: 'published_private',
    verification_state: 'unverified',
    content_format_mix: ['quick_practice_prompt'],
    target_skill_slugs: ['executive-summary', 'concise-explanation', 'structured-communication'],
    target_competency_slugs: ['communication', 'professionalism'],
    rubric_ids: ['quick_practice_text'],
    prompt_items: [PROMPT_ITEMS[0]!],
    scenarios: [],
  },
];

// --- User -------------------------------------------------------------------

export const SEED_CURRENT_USER: UserView = {
  id: 'user-001',
  email: 'alex.chen@example.com',
  display_name: 'Alex Chen',
  role: 'standard_user',
  auth_provider: 'local',
  created_at: '2026-01-15T10:00:00Z',
  profile: {
    target_role: 'Management Consultant',
    goals: ['Improve stakeholder management', 'Prepare for behavioural interviews', 'Build executive presence'],
    practice_preferences: { session_length: '15-30 min', focus_area: 'stakeholder-management' },
  },
};

// --- Practice sessions & attempts ------------------------------------------

export const SEED_ATTEMPT_HISTORY: AttemptHistoryItem[] = [
  { id: 'att-001', session_id: 'sess-001', title: 'Executive Summary: Project Status', practice_type: 'quick_practice', score: 4, skill_slugs: ['executive-summary', 'concise-explanation', 'structured-communication'], created_at: '2026-03-24T14:30:00Z', status: 'assessed' },
  { id: 'att-002', session_id: 'sess-002', title: 'Saying No to Scope Creep', practice_type: 'quick_practice', score: 3, skill_slugs: ['expectation-setting', 'negotiation', 'conflict-handling'], created_at: '2026-03-23T10:15:00Z', status: 'assessed' },
  { id: 'att-003', session_id: 'sess-003', title: 'Active Listening: Team Standup', practice_type: 'quick_practice', score: 5, skill_slugs: ['active-listening', 'empathy', 'structured-communication'], created_at: '2026-03-22T16:45:00Z', status: 'assessed' },
  { id: 'att-004', session_id: 'sess-004', title: 'Tell me about a time you handled conflict', practice_type: 'quick_practice', score: 4, skill_slugs: ['conflict-handling', 'negotiation', 'structured-communication'], created_at: '2026-03-21T09:00:00Z', status: 'assessed' },
  { id: 'att-005', session_id: 'sess-005', title: 'Prioritization Under Pressure', practice_type: 'quick_practice', score: 3, skill_slugs: ['prioritization-under-pressure', 'decision-justification', 'concise-explanation'], created_at: '2026-03-20T11:30:00Z', status: 'assessed' },
  { id: 'att-006', session_id: 'sess-006', title: 'Executive Summary: Project Status', practice_type: 'quick_practice', score: 3, skill_slugs: ['executive-summary', 'concise-explanation', 'structured-communication'], created_at: '2026-03-19T15:00:00Z', status: 'assessed' },
  { id: 'att-007', session_id: 'sess-007', title: 'Active Listening: Team Standup', practice_type: 'quick_practice', score: 4, skill_slugs: ['active-listening', 'empathy', 'structured-communication'], created_at: '2026-03-18T13:20:00Z', status: 'assessed' },
  { id: 'att-008', session_id: 'sess-008', title: 'Saying No to Scope Creep', practice_type: 'quick_practice', score: 2, skill_slugs: ['expectation-setting', 'negotiation', 'conflict-handling'], created_at: '2026-03-17T10:00:00Z', status: 'assessed' },
];

// Derive competency progress from attempt history
export const SEED_COMPETENCY_PROGRESS: CompetencyProgressView[] = SEED_COMPETENCIES.map((comp) => {
  const relevantAttempts = SEED_ATTEMPT_HISTORY.filter((a) =>
    a.skill_slugs.some((s) => comp.skill_slugs.includes(s)),
  );
  const avgScore = relevantAttempts.length > 0
    ? relevantAttempts.reduce((sum, a) => sum + a.score, 0) / relevantAttempts.length
    : 0;

  const skills = comp.skill_slugs.map((slug) => {
    const skill = SEED_SKILLS.find((s) => s.slug === slug)!;
    const skillAttempts = SEED_ATTEMPT_HISTORY.filter((a) => a.skill_slugs.includes(slug));
    const skillAvg = skillAttempts.length > 0
      ? skillAttempts.reduce((s, a) => s + a.score, 0) / skillAttempts.length
      : 0;
    const recent = skillAttempts.slice(0, 2);
    const older = skillAttempts.slice(2);
    const recentAvg = recent.length > 0 ? recent.reduce((s, a) => s + a.score, 0) / recent.length : 0;
    const olderAvg = older.length > 0 ? older.reduce((s, a) => s + a.score, 0) / older.length : 0;
    const trend: 'up' | 'down' | 'stable' = recentAvg > olderAvg + 0.3 ? 'up' : recentAvg < olderAvg - 0.3 ? 'down' : 'stable';

    return {
      slug,
      name: skill.name,
      score: Math.round(skillAvg * 20),
      evidence_count: skillAttempts.length,
      trend,
    };
  });

  const overallScore = Math.round(avgScore * 20);
  const confidence: 'low' | 'medium' | 'high' = relevantAttempts.length >= 4 ? 'high' : relevantAttempts.length >= 2 ? 'medium' : 'low';

  return {
    slug: comp.slug,
    name: comp.name,
    description: comp.description,
    skills,
    overall_score: overallScore,
    confidence,
  };
});
