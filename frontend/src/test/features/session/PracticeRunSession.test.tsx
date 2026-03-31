import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { renderWithRouter, screen, waitFor, userEvent, createMockDataProvider } from '@/test/test-utils';
import { PracticeRunSession } from '@/pages/session/PracticeRunSession';

describe('PracticeRunSession', () => {
  it('advances from one backend scenario step to the next instead of replaying step one', async () => {
    const user = userEvent.setup();

    const runAfterLoad = {
      run_id: 'run-1',
      workflow_id: 'wf-1',
      status: 'active',
      total_items: 2,
      completed_items: 0,
      validated_items: 0,
      failed_items: 0,
      current_attempt_id: 'attempt-1',
      started_at: '2026-03-31T00:00:00Z',
      completed_at: null,
      items: [
        {
          id: 'scenario-step-1',
          item_type: 'scenario',
          title: 'Scenario Step 1',
          prompt_text: 'Question 1 of 2: Identify the stakeholder concerns.',
          difficulty: 'intermediate',
          target_skill_slugs: ['active-listening'],
          status: 'active',
        },
        {
          id: 'scenario-step-2',
          item_type: 'scenario',
          title: 'Scenario Step 2',
          prompt_text: 'Question 2 of 2: Explain your prioritization.',
          difficulty: 'intermediate',
          target_skill_slugs: ['decision-justification'],
          status: 'pending',
        },
      ],
      summary: {
        total_items: 2,
        completed_items: 0,
        overall_score: null,
        score_distribution: {},
        skill_breakdown: {},
        practice_type_breakdown: {},
      },
    } as const;

    const sessions = [
      {
        id: 'prs-1',
        practice_run_id: 'run-1',
        sequence_index: 1,
        content_item_id: 'scenario-1',
        content_item_type: 'scenario',
        attempt_id: 'attempt-1',
        status: 'active',
        score: null,
        started_at: '2026-03-31T00:00:00Z',
        completed_at: null,
      },
      {
        id: 'prs-2',
        practice_run_id: 'run-1',
        sequence_index: 2,
        content_item_id: 'scenario-1',
        content_item_type: 'scenario',
        attempt_id: 'attempt-2',
        status: 'active',
        score: null,
        started_at: '2026-03-31T00:00:00Z',
        completed_at: null,
      },
    ] as const;

    const submitAttempt = vi.fn().mockResolvedValue({
      id: 'attempt-1',
      session_id: 'prs-1',
      workflow_id: 'wf-1',
      status: 'completed',
      response_mode: 'text',
      response_text: 'First scenario step answer',
      last_error_code: null,
      submitted_at: '2026-03-31T00:00:00Z',
      assessed_at: '2026-03-31T00:00:01Z',
      prompt: {
        content_item_id: 'scenario-1',
        prompt_type: 'scenario',
        title: 'Scenario Step 1',
        prompt_text: 'Question 1 of 2: Identify the stakeholder concerns.',
        difficulty: 'intermediate',
        delivery_version: 'v1',
        target_skill_slugs: ['active-listening'],
        rubric_id: 'rubric-1',
        rubric_version: 'v1',
      },
      assessment: {
        assessment_id: 'asm-1',
        attempt_id: 'attempt-1',
        session_id: 'prs-1',
        validation_status: 'validated',
        prompt_version: 'v1',
        rubric_id: 'rubric-1',
        rubric_version: 'v1',
        schema_version: 'v1',
        config_version: 'v1',
        provider: 'test',
        model_slug: 'test',
        overall_score: 4,
        per_skill_assessments: [],
        summary: 'Good response',
        strengths: [],
        weaknesses: [],
        next_actions: [],
        trace_id: 'trace-1',
        pipeline_run_id: 'pipe-1',
        rejection_code: null,
        created_at: '2026-03-31T00:00:01Z',
        raw_payload: {},
      },
    });

    const dataProvider = createMockDataProvider({
      getPracticeRun: vi.fn().mockResolvedValue(runAfterLoad),
      getPracticeSessions: vi.fn().mockResolvedValue(sessions),
      listCollections: vi.fn().mockResolvedValue([
        {
          id: 'collection-1',
          author_user_id: 'user-1',
          organisation_id: 'org-001',
          title: 'Collection',
          summary: 'Summary',
          target_audience: 'Learners',
          difficulty: 'intermediate',
          lifecycle_state: 'published',
          verification_state: 'verified',
          discovery_tier: 'standard',
          source_type: 'manual',
          content_format_mix: ['scenario'],
          target_skill_slugs: ['active-listening'],
          target_competency_slugs: [],
          rubric_ids: ['rubric-1'],
          save_count: 0,
          saved_by_actor: false,
          avg_rating: null,
          rating_count: 0,
          rated_by_actor: null,
          featured: false,
          last_generation_artifact_id: null,
          created_at: '2026-03-31T00:00:00Z',
          updated_at: '2026-03-31T00:00:00Z',
          prompt_items: [],
          scenarios: [
            {
              id: 'scenario-1',
              title: 'Escalation Meeting',
              business_context: 'A delivery is off track.',
              learner_objective: 'De-escalate and align next steps.',
              constraints: ['Time is limited'],
              stakeholder_tensions: ['Sales wants speed'],
              questions: ['How do you open?', 'How do you recover the plan?'],
              lifecycle_state: 'published',
              target_skill_slugs: ['active-listening'],
              rubric_id: 'rubric-1',
              mock_company: null,
              mock_people: [],
              organisation_id: 'org-001',
            },
          ],
        },
      ]),
      submitAttempt,
    });

    renderWithRouter(
      <Routes>
        <Route path="/session/practice-run/:runId" element={<PracticeRunSession />} />
      </Routes>,
      { dataProvider, initialEntries: ['/session/practice-run/run-1'] },
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /scenario step 1/i })).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText(/write your response here/i), 'First scenario step answer');
    await user.click(screen.getByRole('button', { name: /submit response/i }));

    await waitFor(() => {
      expect(submitAttempt).toHaveBeenCalledWith('attempt-1', { response_text: 'First scenario step answer' });
    });

    await waitFor(() => {
      expect(screen.getByText(/response submitted/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /next question/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /scenario step 2/i })).toBeInTheDocument();
    });

    expect(screen.getByText(/question 2 of 2: explain your prioritization\./i)).toBeInTheDocument();
  });
});
