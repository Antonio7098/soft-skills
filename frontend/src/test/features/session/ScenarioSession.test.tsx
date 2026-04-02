import { describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { renderWithRouter, screen, waitFor, userEvent, createMockDataProvider } from '@/test/test-utils';
import { ScenarioSession } from '@/pages/session/ScenarioSession';

describe('ScenarioSession', () => {
  it('steps through scenario questions in order and shows final results', async () => {
    const startSession = {
      session_id: 'sess-1',
      attempt_id: 'att-1',
      status: 'active',
      scenario: {
        id: 'sc-1',
        title: 'Scenario Practice',
        prompt_text: 'Question 1',
        questions: ['Question 1', 'Question 2', 'Question 3'],
        business_context: 'Business context',
        learner_objective: 'Learner objective',
        constraints: [],
        stakeholder_tensions: [],
        lifecycle_state: 'published_private',
        target_skill_slugs: ['structured-communication'],
        rubric_id: 'scenario_text@v1',
        mock_company: null,
        mock_people: [],
      },
      total_steps: 3,
      current_step: 1,
      current_prompt_text: 'Question 1',
      history: [],
      started_at: '2026-04-02T12:00:00Z',
    };
    const secondStep = {
      ...startSession,
      attempt_id: 'att-2',
      current_step: 2,
      current_prompt_text: 'Question 2',
      history: [{ step_number: 1, prompt: 'Question 1', response: 'Response 1' }],
    };
    const completedSession = {
      ...startSession,
      attempt_id: 'att-3',
      current_step: 3,
      current_prompt_text: 'Question 3',
      history: [
        { step_number: 1, prompt: 'Question 1', response: 'Response 1' },
        { step_number: 2, prompt: 'Question 2', response: 'Response 2' },
      ],
    };
    const assessedSession = {
      ...startSession,
      attempt_id: 'att-3',
      status: 'completed',
      current_step: 3,
      current_prompt_text: 'Question 3',
      history: [
        { step_number: 1, prompt: 'Question 1', response: 'Response 1' },
        { step_number: 2, prompt: 'Question 2', response: 'Response 2' },
        { step_number: 3, prompt: 'Question 3', response: 'Response 3' },
      ],
    };
    const finalAttempt = {
      id: 'att-3',
      session_id: 'sess-1',
      workflow_id: 'wf-1',
      status: 'assessed',
      response_mode: 'text',
      response_text: 'Response 3',
      last_error_code: null,
      submitted_at: '2026-04-02T12:05:00Z',
      assessed_at: '2026-04-02T12:05:01Z',
      prompt: {
        practice_type: 'scenario',
        content_item_id: 'sc-1',
        content_item_type: 'scenario_step',
        prompt_type: 'scenario_step',
        title: 'Scenario Practice',
        prompt_text: 'Question 3',
        difficulty: 'intermediate',
        delivery_version: 'scenario.delivery.v1',
        response_mode: 'text',
        target_skill_slugs: ['structured-communication'],
        rubric_id: 'scenario_text@v1',
        rubric_version: 'v1',
      },
      assessment: {
        assessment_id: 'assess-1',
        attempt_id: 'att-3',
        session_id: 'sess-1',
        validation_status: 'validated',
        prompt_version: 'assessment.quick-practice.v1',
        rubric_id: 'scenario_text@v1',
        rubric_version: 'v1',
        schema_version: 'schema-v1',
        config_version: 'config-v1',
        provider: 'openai',
        model_slug: 'gpt-4.1-mini',
        overall_score: 4,
        per_skill_assessments: [],
        skill_scores: [],
        evidence: [],
        rationale: 'Solid response',
        strengths: ['Clear structure'],
        weaknesses: [],
        next_actions: ['Keep tightening recommendations'],
        trace_id: 'trace-1',
        pipeline_run_id: 'pipe-1',
        rejection_code: null,
        created_at: '2026-04-02T12:05:01Z',
      },
    };

    const mockData = createMockDataProvider({
      startScenarioSession: vi.fn().mockResolvedValue(startSession),
      submitScenarioStep: vi.fn()
        .mockResolvedValueOnce(secondStep)
        .mockResolvedValueOnce(completedSession)
        .mockResolvedValueOnce(assessedSession),
      getAttempt: vi.fn().mockResolvedValue(finalAttempt),
    });

    renderWithRouter(
      <Routes>
        <Route path="/session/scenario/:scenarioId" element={<ScenarioSession />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/session/scenario/sc-1'] },
    );

    expect(await screen.findByText('Question 1')).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent === '1/3')).toBeInTheDocument();

    await userEvent.type(screen.getByPlaceholderText('How would you respond in this situation?'), 'Response 1');
    await userEvent.click(screen.getByRole('button', { name: 'Next Question' }));

    await waitFor(() => {
      expect(screen.getByText('Question 2')).toBeInTheDocument();
      expect(screen.getByText((_, element) => element?.textContent === '2/3')).toBeInTheDocument();
    });

    await userEvent.clear(screen.getByPlaceholderText('How would you respond in this situation?'));
    await userEvent.type(screen.getByPlaceholderText('How would you respond in this situation?'), 'Response 2');
    await userEvent.click(screen.getByRole('button', { name: 'Next Question' }));

    await waitFor(() => {
      expect(screen.getByText('Question 3')).toBeInTheDocument();
      expect(screen.getByText((_, element) => element?.textContent === '3/3')).toBeInTheDocument();
    });

    await userEvent.clear(screen.getByPlaceholderText('How would you respond in this situation?'));
    await userEvent.type(screen.getByPlaceholderText('How would you respond in this situation?'), 'Response 3');
    await userEvent.click(screen.getByRole('button', { name: 'Submit Response' }));

    await waitFor(() => {
      expect(mockData.getAttempt).toHaveBeenCalledWith('att-3');
    });
    expect(await screen.findByText('Evaluating your scenario performance...')).toBeInTheDocument();
  });
});
