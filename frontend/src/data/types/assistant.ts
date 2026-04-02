export type AssistantSessionStatus = 'active' | 'archived';
export type AssistantTurnStatus = 'pending' | 'running' | 'cancelling' | 'completed' | 'cancelled' | 'failed';
export type AssistantMessageRole = 'user' | 'assistant';
export type AssistantToolCallStatus = 'running' | 'completed' | 'failed' | 'cancelled';

export interface AssistantMessageView {
  readonly id: string;
  readonly turn_id: string;
  readonly role: AssistantMessageRole;
  readonly content: string;
  readonly metadata: Record<string, unknown>;
  readonly created_at: string;
}

export interface AssistantToolCallView {
  readonly id: string;
  readonly turn_id: string;
  readonly tool_name: string;
  readonly status: AssistantToolCallStatus;
  readonly args: Record<string, unknown>;
  readonly result: Record<string, unknown> | null;
  readonly error_code: string | null;
  readonly error_message: string | null;
  readonly child_run_id: string | null;
  readonly started_at: string;
  readonly completed_at: string | null;
}

export interface AssistantTurnView {
  readonly id: string;
  readonly session_id: string;
  readonly workflow_id: string;
  readonly request_id: string | null;
  readonly trace_id: string | null;
  readonly pipeline_run_id: string | null;
  readonly status: AssistantTurnStatus;
  readonly stream_token: string;
  readonly last_error_code: string | null;
  readonly cancel_reason: string | null;
  readonly created_at: string;
  readonly started_at: string | null;
  readonly completed_at: string | null;
  readonly cancelled_at: string | null;
  readonly user_message_id: string | null;
  readonly assistant_message_id: string | null;
  readonly messages: AssistantMessageView[];
  readonly tool_calls: AssistantToolCallView[];
}

export interface AssistantSessionView {
  readonly id: string;
  readonly user_id: string;
  readonly title: string | null;
  readonly status: AssistantSessionStatus;
  readonly created_at: string;
  readonly updated_at: string;
  readonly turns: AssistantTurnView[];
  readonly messages: AssistantMessageView[];
}

export interface CreateAssistantSessionCommand {
  readonly title?: string;
}

export interface CreateAssistantTurnCommand {
  readonly message: string;
}

export interface CancelAssistantTurnCommand {
  readonly reason?: string;
}

export interface AssistantStreamEvent {
  readonly event_id: string;
  readonly session_id: string;
  readonly type: string;
  readonly turn_id: string;
  readonly trace_id: string | null;
  readonly workflow_id: string | null;
  readonly sequence_number: number;
  readonly emitted_at: string;
  readonly payload: Record<string, unknown>;
}

export interface AssistantStreamControlMessage {
  readonly type: string;
  readonly reason?: string;
}

export interface AssistantStreamCallbacks {
  readonly onResponseDelta?: (payload: { index?: number; delta?: string }) => void;
  readonly onResponseCompleted?: (payload: {
    assistant_message_id?: string;
    content?: string;
  }) => void;
  readonly onToolStarted?: (toolCall: AssistantToolCallView) => void;
  readonly onToolUpdated?: (toolCall: AssistantToolCallView) => void;
  readonly onToolCompleted?: (toolCall: AssistantToolCallView) => void;
  readonly onToolFailed?: (toolCall: AssistantToolCallView) => void;
  readonly onTurnCompleted?: () => void;
  readonly onTurnFailed?: (error: { error_code?: string; message?: string }) => void;
  readonly onError?: (error: string) => void;
  readonly onClose?: () => void;
}
