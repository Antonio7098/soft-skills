import type { AssistantSessionView, AssistantTurnView, AssistantMessageView, AssistantToolCallView } from '../types';

function isoDate(offset = 0): string {
  const date = new Date();
  date.setDate(date.getDate() - offset);
  return date.toISOString();
}

export const SEED_TOOL_CALLS: AssistantToolCallView[] = [
  {
    id: 'tc-001',
    turn_id: 'turn-001',
    tool_name: 'list_collections',
    status: 'completed',
    args: { difficulty: 'intermediate' },
    result: {
      collections: [
        { id: 'col-001', title: 'Advanced Negotiation', difficulty: 'intermediate' },
        { id: 'col-002', title: 'Team Communication', difficulty: 'introductory' },
      ],
    },
    error_code: null,
    error_message: null,
    child_run_id: 'run-001',
    started_at: isoDate(1),
    completed_at: isoDate(1),
  },
  {
    id: 'tc-002',
    turn_id: 'turn-001',
    tool_name: 'get_collection',
    status: 'completed',
    args: { collection_id: 'col-001' },
    result: {
      collection: {
        id: 'col-001',
        title: 'Advanced Negotiation Scenarios',
        summary: 'Practice complex negotiation skills with realistic scenarios',
        difficulty: 'intermediate',
      },
    },
    error_code: null,
    error_message: null,
    child_run_id: 'run-002',
    started_at: isoDate(1),
    completed_at: isoDate(1),
  },
  {
    id: 'tc-003',
    turn_id: 'turn-002',
    tool_name: 'start_collection_practice',
    status: 'failed',
    args: { collection_id: 'col-001' },
    result: null,
    error_code: 'SS-PRACTICE-401',
    error_message: 'Collection not found or access denied',
    child_run_id: null,
    started_at: isoDate(0),
    completed_at: isoDate(0),
  },
];

export const SEED_MESSAGES: AssistantMessageView[] = [
  {
    id: 'msg-001',
    turn_id: 'turn-001',
    role: 'user',
    content: 'Can you help me find some negotiation practice exercises?',
    metadata: {},
    created_at: isoDate(1),
  },
  {
    id: 'msg-002',
    turn_id: 'turn-001',
    role: 'assistant',
    content: 'I found some great collection options for you! I can see there\'s an "Advanced Negotiation Scenarios" collection that might be perfect for your needs. Would you like me to get more details about it or start a practice session?',
    metadata: {},
    created_at: isoDate(1),
  },
  {
    id: 'msg-003',
    turn_id: 'turn-002',
    role: 'user',
    content: 'Let me try a different approach. Can you show me collections for team communication?',
    metadata: {},
    created_at: isoDate(0),
  },
];

export const SEED_TURNS: AssistantTurnView[] = [
  {
    id: 'turn-001',
    session_id: 'session-001',
    workflow_id: 'wf-001',
    request_id: 'req-001',
    trace_id: 'trace-001',
    pipeline_run_id: 'pr-001',
    status: 'completed',
    stream_token: 'st-abc123',
    last_error_code: null,
    cancel_reason: null,
    created_at: isoDate(1),
    started_at: isoDate(1),
    completed_at: isoDate(1),
    cancelled_at: null,
    user_message_id: 'msg-001',
    assistant_message_id: 'msg-002',
    messages: [SEED_MESSAGES[0]!, SEED_MESSAGES[1]!],
    tool_calls: [SEED_TOOL_CALLS[0]!, SEED_TOOL_CALLS[1]!],
  },
  {
    id: 'turn-002',
    session_id: 'session-001',
    workflow_id: 'wf-002',
    request_id: 'req-002',
    trace_id: 'trace-002',
    pipeline_run_id: 'pr-002',
    status: 'failed',
    stream_token: 'st-def456',
    last_error_code: 'SS-PRACTICE-401',
    cancel_reason: null,
    created_at: isoDate(0),
    started_at: isoDate(0),
    completed_at: isoDate(0),
    cancelled_at: null,
    user_message_id: 'msg-003',
    assistant_message_id: null,
    messages: [SEED_MESSAGES[2]!],
    tool_calls: [SEED_TOOL_CALLS[2]!],
  },
];

export const SEED_ASSISTANT_SESSIONS: AssistantSessionView[] = [
  {
    id: 'session-001',
    user_id: 'usr-001',
    title: 'Negotiation Practice Session',
    status: 'active',
    created_at: isoDate(7),
    updated_at: isoDate(0),
    turns: [SEED_TURNS[0]!, SEED_TURNS[1]!],
    messages: [SEED_MESSAGES[0]!, SEED_MESSAGES[1]!, SEED_MESSAGES[2]!],
  },
  {
    id: 'session-002',
    user_id: 'usr-001',
    title: 'Communication Skills Help',
    status: 'active',
    created_at: isoDate(14),
    updated_at: isoDate(14),
    turns: [],
    messages: [],
  },
  {
    id: 'session-003',
    user_id: 'usr-001',
    title: 'Quick Practice Questions',
    status: 'archived',
    created_at: isoDate(30),
    updated_at: isoDate(21),
    turns: [],
    messages: [],
  },
];
