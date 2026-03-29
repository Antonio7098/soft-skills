export interface LearnerProfileView {
  readonly target_role: string | null;
  readonly goals: string[];
  readonly practice_preferences: Record<string, string>;
}

export interface UserView {
  readonly id: string;
  readonly email: string;
  readonly display_name: string;
  readonly role: string;
  readonly auth_provider: string;
  readonly created_at: string;
  readonly profile: LearnerProfileView;
}

export interface RegisterUserCommand {
  readonly email: string;
  readonly display_name: string;
  readonly role?: string;
  readonly target_role?: string;
  readonly goals?: string[];
  readonly practice_preferences?: Record<string, string>;
}

export interface UpdateProfileCommand {
  readonly target_role?: string | null;
  readonly goals?: string[] | null;
  readonly practice_preferences?: Record<string, string> | null;
}
