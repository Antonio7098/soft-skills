import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { renderWithRouter, screen, waitFor, act, userEvent, createMockDataProvider } from '@/test/test-utils';
import { ScenarioSession } from '@/pages/session/ScenarioSession';

describe('ScenarioSession', () => {
  it('preserves draft text across timer re-renders and advances to the next question on submit', async () => {
    const user = userEvent.setup();

    const scenario = {
      id: 'scenario-1',
      title: 'Escalation Meeting',
      business_context: 'A delivery is off track.',
      learner_objective: 'De-escalate and align next steps.',
      constraints: ['Time is limited'],
      stakeholder_tensions: ['Sales wants speed', 'Engineering wants scope control'],
      questions: ['How do you open?', 'How do you recover the plan?'],
      lifecycle_state: 'published',
      target_skill_slugs: ['active-listening'],
      rubric_id: 'rubric-1',
      mock_company: null,
      mock_people: [],
      organisation_id: 'org-001',
    } as const;

    const collection = {
      id: 'collection-1',
      author_user_id: 'user-1',
      organisation_id: 'org-001',
      title: 'Scenario Collection',
      summary: 'Test collection',
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
      scenarios: [scenario],
    } as const;

    const startScenarioSession = vi.fn().mockResolvedValue({
      attempt_id: 'attempt-1',
      session_id: 'session-1',
    });
    const submitAttempt = vi.fn().mockResolvedValue({
      attempt_id: 'attempt-1',
      session_id: 'session-1',
      status: 'completed',
      prompt: {
        title: 'Question 1',
        prompt_text: scenario.questions[0],
        difficulty: 'intermediate',
        target_skill_slugs: ['active-listening'],
      },
      response_text: 'This is a sufficiently long scenario answer.',
      assessment: {
        overall_score: 1,
        summary: 'Solid response',
        strengths: [],
        weaknesses: [],
        rubric_id: 'rubric-1',
      },
      submitted_at: '2026-03-31T00:00:00Z',
      assessed_at: '2026-03-31T00:00:01Z',
    });

    const dataProvider = createMockDataProvider({
      listCollections: vi.fn().mockResolvedValue([collection]),
      startScenarioSession,
      submitAttempt,
    });

    renderWithRouter(
      <Routes>
        <Route path="/session/scenario/:scenarioId" element={<ScenarioSession />} />
      </Routes>,
      { dataProvider, initialEntries: ['/session/scenario/scenario-1'] },
    );

    await waitFor(() => {
      expect(screen.getByText(/question 1 of 2/i)).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/how would you respond in this situation/i);
    const answer = 'This is a sufficiently long scenario answer.';
    await user.type(textarea, answer);
    expect(textarea).toHaveValue(answer);

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1200));
    });

    expect(textarea).toHaveValue(answer);

    await user.click(screen.getByRole('button', { name: /submit & continue/i }));

    await waitFor(() => {
      expect(screen.getByText(/question 2 of 2/i)).toBeInTheDocument();
    });

    expect(startScenarioSession).toHaveBeenCalledTimes(1);
    expect(submitAttempt).toHaveBeenCalledTimes(1);
  });
});
