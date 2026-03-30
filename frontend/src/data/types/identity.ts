export interface LearnerProfileView {
  readonly target_role: string | null;
  readonly goals: string[];
  readonly practice_preferences: Record<string, string>;
}

export type PlatformRole = 'anonymous' | 'learner' | 'admin' | 'superadmin';

export type OrganisationRole = 'member' | 'org_admin';

export interface OrganisationMembershipView {
  readonly organisation_id: string;
  readonly organisation_name: string;
  readonly role: OrganisationRole;
  readonly permissions: string[];
}

export interface AuthSessionView {
  readonly status: 'anonymous' | 'authenticated';
  readonly actor: UserView | null;
  readonly platform_role: PlatformRole;
  readonly org_memberships: OrganisationMembershipView[];
  readonly active_organisation_id: string | null;
  readonly capabilities: string[];
  readonly data_mode: 'api' | 'mock';
}

export interface AuthProfileView {
  readonly id: string;
  readonly label: string;
  readonly description: string;
  readonly session: AuthSessionView;
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
  readonly password?: string;
  readonly role?: string;
  readonly target_role?: string;
  readonly goals?: string[];
  readonly practice_preferences?: Record<string, string>;
}

export interface LoginUserCommand {
  readonly email: string;
  readonly password: string;
}

export interface UpdateProfileCommand {
  readonly target_role?: string | null;
  readonly goals?: string[] | null;
  readonly practice_preferences?: Record<string, string> | null;
}

export interface DeleteAccountResult {
  readonly deleted_user_id: string;
  readonly status: string;
}
